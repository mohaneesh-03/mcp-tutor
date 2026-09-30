import asyncio
import json
import logging
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Optional, Dict, Any
from mcp_tutor.models import QuizRequest, QuizResult, AskRequest, AskResult, DONT_KNOW_VALUE, DONT_KNOW_LABEL

logger = logging.getLogger("mcp_tutor.ui")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Socratic Tutor Diagnostic</title>
  <!-- KaTeX for math rendering -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
          onload="renderMath()"></script>
  <style>
    :root {
      --bg: #0d1117;
      --card-bg: #161b22;
      --border: #30363d;
      --text: #c9d1d9;
      --text-bright: #f0f6fc;
      --accent: #58a6ff;
      --success: #238636;
      --success-bg: rgba(35, 134, 54, 0.15);
      --danger: #da3633;
      --danger-bg: rgba(218, 54, 51, 0.15);
      --highlight: #21262d;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      padding: 24px;
    }
    .modal {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      width: 100%;
      max-width: 680px;
      padding: 32px;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
      animation: fadeIn 0.2s ease-out;
    }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
    .badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      background: rgba(88, 166, 255, 0.15);
      color: var(--accent);
      margin-bottom: 16px;
    }
    .context {
      font-size: 14px;
      color: #8b949e;
      margin-bottom: 12px;
      line-height: 1.5;
    }
    .question {
      font-size: 20px;
      font-weight: 600;
      color: var(--text-bright);
      margin-bottom: 24px;
      line-height: 1.4;
    }
    .options-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin-bottom: 24px;
    }
    .option-btn {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 16px;
      background: var(--highlight);
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--text);
      font-size: 15px;
      text-align: left;
      cursor: pointer;
      transition: all 0.15s ease;
      position: relative;
    }
    .option-btn:hover, .option-btn.selected {
      background: #282e37;
      border-color: var(--accent);
      color: var(--text-bright);
    }
    .key-hint {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 24px;
      height: 24px;
      border-radius: 4px;
      background: rgba(255, 255, 255, 0.1);
      font-size: 12px;
      font-weight: bold;
      color: #8b949e;
      flex-shrink: 0;
    }
    .dont-know-btn {
      border-style: dashed;
      color: #8b949e;
      background: transparent;
    }
    .dont-know-btn:hover, .dont-know-btn.selected {
      border-color: #8b949e;
      color: var(--text-bright);
      background: rgba(255, 255, 255, 0.05);
    }
    .note-input {
      width: 100%;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 10px 14px;
      color: var(--text-bright);
      font-size: 14px;
      margin-bottom: 24px;
      outline: none;
    }
    .note-input:focus { border-color: var(--accent); }
    .actions {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .submit-btn {
      background: var(--accent);
      color: #0d1117;
      border: none;
      padding: 12px 24px;
      border-radius: 6px;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      transition: opacity 0.2s;
    }
    .submit-btn:disabled { opacity: 0.4; cursor: not-allowed; }
    .submit-btn:hover:not(:disabled) { opacity: 0.9; }

    /* Result State */
    .result-box {
      display: none;
      padding: 20px;
      border-radius: 8px;
      margin-top: 20px;
      border: 1px solid;
    }
    .result-box.correct {
      background: var(--success-bg);
      border-color: var(--success);
      color: #3fb950;
    }
    .result-box.incorrect {
      background: var(--danger-bg);
      border-color: var(--danger);
      color: #f85149;
    }
    .result-box.dont_know {
      background: rgba(255, 255, 255, 0.05);
      border-color: #8b949e;
      color: #c9d1d9;
    }
    .explanation-text {
      color: var(--text);
      font-size: 14.5px;
      line-height: 1.6;
      margin-top: 10px;
    }
    .continue-btn {
      margin-top: 16px;
      background: var(--highlight);
      border: 1px solid var(--border);
      color: var(--text-bright);
      padding: 10px 20px;
      border-radius: 6px;
      font-size: 14px;
      cursor: pointer;
    }
    .continue-btn:hover { background: #30363d; }
  </style>
</head>
<body>

<div class="modal">
  <div class="badge" id="typeBadge">Diagnostic Check</div>
  <div class="context" id="contextBlock" style="display: none;"></div>
  <h2 class="question" id="questionText"></h2>

  <div class="options-list" id="optionsList"></div>

  <input type="text" class="note-input" id="studentNote" placeholder="Optional reasoning or note..." />

  <div class="actions" id="actionRow">
    <span style="font-size: 12px; color: #8b949e;">Use number keys [1-9], [0] for IDK, [Enter] to submit</span>
    <button class="submit-btn" id="submitBtn" disabled>Submit Answer</button>
  </div>

  <div class="result-box" id="resultBox">
    <h3 id="resultTitle" style="margin-bottom: 8px;"></h3>
    <div class="explanation-text" id="explanationText"></div>
    <button class="continue-btn" id="continueBtn">Continue Lesson [Enter]</button>
  </div>
</div>

<script>
  let data = __PAYLOAD_DATA__;
  let selectedIndex = -1;
  let isAnswered = false;

  function renderMath() {
    if (window.renderMathInElement) {
      renderMathInElement(document.body, {
        delimiters: [
          {left: '$$', right: '$$', display: true},
          {left: '$', right: '$', display: false}
        ]
      });
    }
  }

  function initUI() {
    document.getElementById('questionText').textContent = data.question;
    if (data.context) {
      const cBlock = document.getElementById('contextBlock');
      cBlock.textContent = data.context;
      cBlock.style.display = 'block';
    }

    const list = document.getElementById('optionsList');
    list.innerHTML = '';

    data.options.forEach((opt, idx) => {
      const btn = document.createElement('div');
      btn.className = 'option-btn' + (opt.is_dont_know ? ' dont-know-btn' : '');
      btn.id = 'opt-' + idx;
      
      const key = opt.is_dont_know ? '0' : (idx + 1);
      btn.innerHTML = `
        <span class="key-hint">${key}</span>
        <span style="flex: 1;">${opt.label}</span>
      `;
      btn.onclick = () => selectOption(idx);
      list.appendChild(btn);
    });

    renderMath();
  }

  function selectOption(idx) {
    if (isAnswered) return;
    selectedIndex = idx;
    data.options.forEach((_, i) => {
      const el = document.getElementById('opt-' + i);
      if (el) el.classList.toggle('selected', i === idx);
    });
    document.getElementById('submitBtn').disabled = false;
  }

  async function submit() {
    if (selectedIndex === -1 || isAnswered) return;
    isAnswered = true;

    const opt = data.options[selectedIndex];
    const isDontKnow = !!opt.is_dont_know;
    const isCorrect = !isDontKnow && (selectedIndex === data.correct_index);
    const note = document.getElementById('studentNote').value.trim();

    // Show result locally
    const resBox = document.getElementById('resultBox');
    const title = document.getElementById('resultTitle');
    const exp = document.getElementById('explanationText');

    document.getElementById('actionRow').style.display = 'none';
    document.getElementById('studentNote').style.display = 'none';

    if (isDontKnow) {
      resBox.className = 'result-box dont_know';
      title.textContent = 'Acknowledged — Zero Guesses';
      exp.innerHTML = `<strong>Ground Truth:</strong> ${data.options[data.correct_index].label}<br><br>${data.explanation}`;
    } else if (isCorrect) {
      resBox.className = 'result-box correct';
      title.textContent = '✓ Correct Understanding';
      exp.innerHTML = data.explanation;
    } else {
      resBox.className = 'result-box incorrect';
      title.textContent = '✗ Diagnostic Gap Identified';
      exp.innerHTML = `<strong>Correct Answer:</strong> ${data.options[data.correct_index].label}<br><br>${data.explanation}`;
    }
    resBox.style.display = 'block';
    renderMath();

    // Post to local server
    await fetch('/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        selected_index: isDontKnow ? -1 : selectedIndex,
        selected_label: opt.label,
        is_correct: isCorrect,
        dont_know: isDontKnow,
        student_notes: note || null
      })
    });
  }

  function completeAndClose() {
    window.close();
  }

  document.getElementById('submitBtn').onclick = submit;
  document.getElementById('continueBtn').onclick = completeAndClose;

  window.addEventListener('keydown', (e) => {
    if (isAnswered) {
      if (e.key === 'Enter' || e.key === ' ') completeAndClose();
      return;
    }
    if (e.key >= '1' && e.key <= '9') {
      const num = parseInt(e.key) - 1;
      if (num < data.options.length - 1) selectOption(num);
    } else if (e.key === '0' || e.key.toLowerCase() === 'd') {
      // Pick IDK
      selectOption(data.options.length - 1);
    } else if (e.key === 'Enter') {
      if (selectedIndex !== -1) submit();
    }
  });

  initUI();
</script>
</body>
</html>
"""

class QuizServer:
    def __init__(self, port: int = 7331):
        self.port = port
        self.current_payload: Optional[Dict[str, Any]] = None
        self.response_future: Optional[asyncio.Future] = None
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[Thread] = None
        self.loop = asyncio.get_event_loop()

    def start(self):
        if self.server:
            return

        parent = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # Silence HTTP logs

            def do_GET(self):
                if self.path == "/" or self.path.startswith("/?"):
                    if not parent.current_payload:
                        self.send_response(200)
                        self.send_header("Content-Type", "text/html")
                        self.end_headers()
                        self.wfile.write(b"<h1>No active question. Waiting for tutor...</h1>")
                        return

                    rendered = HTML_TEMPLATE.replace(
                        "__PAYLOAD_DATA__", json.dumps(parent.current_payload)
                    )
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(rendered.encode("utf-8"))
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_POST(self):
                if self.path == "/submit":
                    length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(length)
                    data = json.loads(body.decode("utf-8"))

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(b'{"status":"ok"}')

                    if parent.response_future and not parent.response_future.done():
                        parent.loop.call_soon_threadsafe(
                            parent.response_future.set_result, data
                        )

        self.server = HTTPServer(("127.0.0.1", self.port), Handler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        logger.info(f"Interactive quiz UI server running at http://127.0.0.1:{self.port}")

    async def ask_quiz(self, req: QuizRequest, auto_open: bool = True) -> QuizResult:
        self.start()

        # Build options with mandatory "I don't know" choice
        display_options = []
        for i, opt in enumerate(req.options):
            display_options.append({
                "label": opt,
                "value": str(i),
                "is_dont_know": False
            })
        
        # Append "I don't know"
        display_options.append({
            "label": DONT_KNOW_LABEL,
            "value": DONT_KNOW_VALUE,
            "is_dont_know": True
        })

        self.current_payload = {
            "question": req.question,
            "context": req.context,
            "options": display_options,
            "correct_index": req.correct_index,
            "explanation": req.explanation
        }

        self.response_future = self.loop.create_future()

        if auto_open:
            webbrowser.open(f"http://127.0.0.1:{self.port}")

        # Await submission from browser
        res_data = await self.response_future

        selected_idx = res_data["selected_index"]
        is_dont_know = res_data["dont_know"]
        is_correct = res_data["is_correct"]
        notes = res_data.get("student_notes")

        correct_label = req.options[req.correct_index]
        selected_label = DONT_KNOW_LABEL if is_dont_know else req.options[selected_idx]

        msg = (
            "✓ Learner answered correctly!"
            if is_correct
            else ("Learner selected 'I don't know' (honest gap, no guesswork)."
                  if is_dont_know else f"✗ Misconception: learner chose '{selected_label}'.")
        )

        return QuizResult(
            status="answered",
            question=req.question,
            selected_index=selected_idx,
            selected_label=selected_label,
            is_correct=is_correct,
            dont_know=is_dont_know,
            correct_index=req.correct_index,
            correct_label=correct_label,
            explanation=req.explanation,
            student_notes=notes,
            message=msg
        )

# Global UI instance
QUIZ_SERVER = QuizServer()
