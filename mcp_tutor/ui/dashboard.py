import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from threading import Thread
import webbrowser

logger = logging.getLogger("mcp_tutor.dashboard")

class DashboardState:
    def __init__(self):
        self.topic: str = "Awaiting Learning Session..."
        self.blocks: List[Dict[str, Any]] = []  # Chronological items: 'prose', 'diagram', 'quiz'
        self.active_quiz: Optional[Dict[str, Any]] = None
        self.active_quiz_future: Optional[asyncio.Future] = None
        self.mermaid_dag: str = ""
        self.stats = {
            "total_checks": 0,
            "correct": 0,
            "misconceptions": 0,
            "dont_know": 0
        }
        self.connected_clients: List[WebSocket] = []
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "blocks": self.blocks,
            "active_quiz": self.active_quiz,
            "mermaid_dag": self.mermaid_dag,
            "stats": self.stats
        }

    async def broadcast(self, message: Dict[str, Any]):
        for client in list(self.connected_clients):
            try:
                await client.send_json(message)
            except Exception:
                if client in self.connected_clients:
                    self.connected_clients.remove(client)

STATE = DashboardState()
app = FastAPI(title="MCP Tutor Dashboard")

# HTML Template will be loaded from index.html
TEMPLATE_PATH = Path(__file__).parent / "templates" / "index.html"

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    if TEMPLATE_PATH.exists():
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Dashboard template not found. Please restart server.</h1>"

@app.get("/api/state")
async def get_state():
    return JSONResponse(STATE.to_dict())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    STATE.connected_clients.append(websocket)
    # Send full initial snapshot
    await websocket.send_json({"type": "sync_state", "data": STATE.to_dict()})
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            if msg_type == "quiz_submit":
                if STATE.active_quiz_future and not STATE.active_quiz_future.done():
                    STATE.active_quiz_future.set_result(data)
    except WebSocketDisconnect:
        if websocket in STATE.connected_clients:
            STATE.connected_clients.remove(websocket)

class DashboardServer:
    def __init__(self, port: int = 7331):
        self.port = port
        self.thread: Optional[Thread] = None
        self.server: Optional[uvicorn.Server] = None
        self._started = False

    def start(self):
        if self._started:
            return
        self._started = True

        def run_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            STATE.loop = loop
            config = uvicorn.Config(
                app=app,
                host="127.0.0.1",
                port=self.port,
                log_level="warning",
                access_log=False
            )
            self.server = uvicorn.Server(config)
            loop.run_until_complete(self.server.serve())

        self.thread = Thread(target=run_server, daemon=True)
        self.thread.start()
        logger.info(f"All-in-one dashboard server running at http://127.0.0.1:{self.port}")

    def ensure_open_browser(self):
        self.start()
        try:
            webbrowser.open(f"http://127.0.0.1:{self.port}")
        except Exception:
            pass

    async def init_session(self, topic: str):
        self.start()
        STATE.topic = topic
        STATE.blocks = []
        STATE.active_quiz = None
        STATE.mermaid_dag = ""
        STATE.stats = {"total_checks": 0, "correct": 0, "misconceptions": 0, "dont_know": 0}
        await STATE.broadcast({"type": "session_init", "data": STATE.to_dict()})

    async def append_prose(self, text: str):
        self.start()
        block = {"type": "prose", "content": text}
        STATE.blocks.append(block)
        await STATE.broadcast({"type": "append_prose", "block": block})

    async def append_diagram(self, diagram_type: str, code: str, title: Optional[str] = None):
        self.start()
        block = {
            "type": "diagram",
            "diagram_type": diagram_type,
            "code": code.strip(),
            "title": title
        }
        STATE.blocks.append(block)
        if diagram_type == "mermaid" and ("graph " in code or "flowchart " in code):
            STATE.mermaid_dag = code.strip()
        await STATE.broadcast({"type": "append_diagram", "block": block, "mermaid_dag": STATE.mermaid_dag})

    async def pose_quiz(self, quiz_data: Dict[str, Any], auto_open: bool = True) -> Dict[str, Any]:
        self.start()
        if auto_open:
            self.ensure_open_browser()

        # Build options with mandatory "I don't know" choice
        options = []
        for i, opt in enumerate(quiz_data["options"]):
            options.append({
                "label": opt,
                "value": str(i),
                "is_dont_know": False
            })
        options.append({
            "label": "I don't know / Not sure",
            "value": "__dont_know__",
            "is_dont_know": True
        })

        quiz_id = f"quiz_{len(STATE.blocks)}"
        active_quiz = {
            "id": quiz_id,
            "question": quiz_data["question"],
            "context": quiz_data.get("context"),
            "options": options,
            "correct_index": quiz_data["correct_index"],
            "explanation": quiz_data["explanation"]
        }

        STATE.active_quiz = active_quiz
        # Place placeholder in blocks list so it appears in the live flow
        block = {"type": "quiz", "data": active_quiz, "resolved": False}
        STATE.blocks.append(block)

        # Create future on the dashboard event loop or current loop
        loop = STATE.loop or asyncio.get_event_loop()
        STATE.active_quiz_future = loop.create_future()

        await STATE.broadcast({"type": "quiz_prompt", "quiz": active_quiz})

        # Await learner submission from browser via WebSocket
        submission = await STATE.active_quiz_future

        # Process and resolve
        selected_idx = submission["selected_index"]
        is_dont_know = submission["dont_know"]
        is_correct = submission["is_correct"]
        notes = submission.get("student_notes")

        correct_label = quiz_data["options"][quiz_data["correct_index"]]
        selected_label = "I don't know / Not sure" if is_dont_know else quiz_data["options"][selected_idx]

        # Update stats
        STATE.stats["total_checks"] += 1
        if is_correct:
            STATE.stats["correct"] += 1
        elif is_dont_know:
            STATE.stats["dont_know"] += 1
        else:
            STATE.stats["misconceptions"] += 1

        resolved_payload = {
            "id": quiz_id,
            "is_correct": is_correct,
            "dont_know": is_dont_know,
            "selected_index": selected_idx,
            "selected_label": selected_label,
            "correct_index": quiz_data["correct_index"],
            "correct_label": correct_label,
            "explanation": quiz_data["explanation"],
            "student_notes": notes
        }

        # Mark block as resolved
        block["resolved"] = True
        block["result"] = resolved_payload
        STATE.active_quiz = None

        await STATE.broadcast({"type": "quiz_resolved", "resolution": resolved_payload, "stats": STATE.stats})

        msg = (
            "✓ Learner answered correctly!"
            if is_correct
            else ("Learner selected 'I don't know' (honest gap, zero guesswork)."
                  if is_dont_know else f"✗ Misconception: learner chose '{selected_label}'.")
        )

        return {
            "status": "answered",
            "question": quiz_data["question"],
            "selected_index": selected_idx,
            "selected_label": selected_label,
            "is_correct": is_correct,
            "dont_know": is_dont_know,
            "correct_index": quiz_data["correct_index"],
            "correct_label": correct_label,
            "explanation": quiz_data["explanation"],
            "student_notes": notes,
            "message": msg
        }

DASHBOARD = DashboardServer()
