import asyncio
import sys
from pathlib import Path
from typing import List, Optional
from mcp.server.fastmcp import FastMCP

from mcp_tutor.config import CONFIG
from mcp_tutor.models import QuizRequest, QuizResult, AskRequest, AskResult
from mcp_tutor.engine.quiz import run_quiz
from mcp_tutor.engine.logger import LOGGER
from mcp_tutor.engine.visuals import VISUALS
from mcp_tutor.ui.dashboard import DASHBOARD

# Initialize FastMCP Server
mcp = FastMCP(
    name="mcp-tutor",
    instructions=(
        "Universal Active Learning & Socratic Tutoring Server with an All-in-One Live Web Dashboard. "
        "The learner views notes, LaTeX math, interactive Mermaid DAGs, and answers quizzes at http://127.0.0.1:7331. "
        "Use pose_quiz for all diagnostic checks (single-node confirmation, edge bracketing). "
        "Use ask_learner for open-ended preferences and goal clarification. "
        "Use init_session to start the live dashboard and mirrored markdown note."
    )
)

@mcp.tool()
async def init_session(topic: str, vault_dir: Optional[str] = None) -> str:
    """
    Initializes the all-in-one live learning dashboard (http://127.0.0.1:7331)
    and creates a corresponding markdown note. Call this at the start of any teaching session.
    
    Args:
        topic: The title of the subject (e.g. 'Self-Attention Mechanism', 'Fourier Transform')
        vault_dir: Optional custom path to Obsidian vault / notes directory
    """
    if vault_dir:
        LOGGER.vault_dir = Path(vault_dir)
    target = await LOGGER.init_session(topic=topic)
    await DASHBOARD.init_session(topic=topic)
    if CONFIG.auto_open_browser:
        DASHBOARD.ensure_open_browser()
    return f"Live Learning Dashboard active at http://127.0.0.1:7331. Note mirrored at: {target}"

@mcp.tool()
async def pose_quiz(
    question: str,
    options: List[str],
    correct_index: int,
    explanation: str,
    context: Optional[str] = None
) -> dict:
    """
    Presents an interactive, graded diagnostic question inside the All-in-One Live Dashboard.
    Features:
    - Zero '(Recommended)' giveaways: options are rendered neutrally with numbers [1-9].
    - Injects 'I don't know / Not sure' to prevent guesswork from corrupting the diagnostic signal.
    - Appends question to the live note immediately, hiding the answer until submitted (Delayed Reveal).
    - Renders LaTeX equations in both questions and explanations ($f(x)$ or $$...$$).
    - Returns diagnostic outcome (is_correct, dont_know, misconception details) to the tutor.
    
    Rules for Options:
    - Every option must be a bare claim (zero 'because' or justifications in options).
    - All reasoning belongs in the 'explanation' field.
    - No asymmetric bolding.
    """
    req = QuizRequest(
        question=question,
        options=options,
        correct_index=correct_index,
        explanation=explanation,
        context=context
    )

    # 1. Delayed reveal: append question to Obsidian log without answer
    await LOGGER.append_question_unresolved(req)

    # 2. Trigger interactive UI in the All-in-One Dashboard
    result, warnings = await run_quiz(req, auto_open=CONFIG.auto_open_browser)

    # 3. Resolve and record student's answer and explanation in Obsidian log
    await LOGGER.resolve_question(result)

    response = result.model_dump()
    if warnings:
        response["distractor_warnings"] = warnings

    return response

@mcp.tool()
async def ask_learner(
    prompt: str,
    options: Optional[List[str]] = None,
    mode: str = "free-text"
) -> dict:
    """
    Asks the learner an open-ended question, goal clarification, or preference choice.
    Used for Phase 1b (discovering the learner's true goal) or branching decisions.
    Unlike pose_quiz, this has no correct answer or grading.
    """
    req = AskRequest(prompt=prompt, options=options, mode=mode)
    
    # Broadcast to dashboard & log to note
    prose = f"> [!QUESTION] **Direction Check**\n> {prompt}\n"
    if options:
        for opt in options:
            prose += f"> - {opt}\n"
    await LOGGER.append_prose(prose)
    await DASHBOARD.append_prose(prose)

    return {
        "status": "prompted",
        "prompt": prompt,
        "mode": mode,
        "options": options or []
    }

@mcp.tool()
async def log_prose(text: str) -> str:
    """
    Streams lesson prose or explanations to the live web dashboard and active note.
    Supports standard Markdown and LaTeX math ($f(x)$ or $$...$$).
    """
    await LOGGER.append_prose(text)
    await DASHBOARD.append_prose(text)
    return "Prose streamed to dashboard and note."

@mcp.tool()
async def publish_diagram(diagram_type: str, code: str, slug: str) -> dict:
    """
    Publishes a Mermaid or SVG diagram into the active learning dashboard
    and embeds it into the live lesson note.
    
    Args:
        diagram_type: 'mermaid' or 'svg'
        code: The diagram source code
        slug: Short kebab-case identifier (e.g. 'attention-dag')
    """
    res = VISUALS.publish_diagram(
        vault_dir=LOGGER.vault_dir,
        diagram_type=diagram_type,
        code=code,
        slug=slug
    )
    # Append to active log & dashboard
    await LOGGER.append_diagram(diagram_type=diagram_type, code=code, title=slug)
    await DASHBOARD.append_diagram(diagram_type=diagram_type, code=code, title=slug)
    return res

def main():
    DASHBOARD.start()
    mcp.run()

if __name__ == "__main__":
    main()
