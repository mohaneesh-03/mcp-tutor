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

# Initialize FastMCP Server
mcp = FastMCP(
    name="mcp-tutor",
    instructions=(
        "Universal Active Learning & Socratic Tutoring Server. "
        "Use pose_quiz for all diagnostic checks (single-node confirmation, edge bracketing). "
        "Use ask_learner for open-ended preferences and goal clarification. "
        "Use init_session to start a live mirrored markdown note in Obsidian."
    )
)

@mcp.tool()
async def init_session(topic: str, vault_dir: Optional[str] = None) -> str:
    """
    Initializes a new live active-learning session note in Obsidian.
    Call this at the beginning of any teaching session.
    
    Args:
        topic: The title of the subject (e.g. 'Fourier Transform', 'Paxos Consensus')
        vault_dir: Optional custom path to Obsidian vault / notes directory
    """
    if vault_dir:
        LOGGER.vault_dir = Path(vault_dir)
    target = await LOGGER.init_session(topic=topic)
    return f"Active learning session started. Live note created at: {target}"

@mcp.tool()
async def pose_quiz(
    question: str,
    options: List[str],
    correct_index: int,
    explanation: str,
    context: Optional[str] = None
) -> dict:
    """
    Presents an interactive, graded diagnostic question to the learner.
    Features:
    - Injects 'I don't know' to prevent guessing from corrupting the diagnostic signal.
    - Appends question to the live Obsidian note immediately, hiding the answer until submitted.
    - Displays a sleek interactive modal for the learner.
    - Returns diagnostic outcome (is_correct, dont_know, misconception details).
    
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

    # 2. Trigger interactive UI modal
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
    
    # Also log to Obsidian note
    prose = f"> [!QUESTION] **Direction Check**\n> {prompt}\n"
    if options:
        for opt in options:
            prose += f"> - {opt}\n"
    await LOGGER.append_prose(prose)

    # For now, return prompt signal (or interactive prompt)
    return {
        "status": "prompted",
        "prompt": prompt,
        "mode": mode,
        "options": options or []
    }

@mcp.tool()
async def log_prose(text: str) -> str:
    """
    Appends lesson prose or explanations to the active Obsidian note.
    Supports standard Markdown and LaTeX math ($f(x)$ or $$...$$).
    """
    await LOGGER.append_prose(text)
    return "Prose appended to active note."

@mcp.tool()
async def publish_diagram(diagram_type: str, code: str, slug: str) -> dict:
    """
    Publishes a Mermaid or SVG diagram into the active Obsidian vault
    and embeds it into the live lesson note.
    
    Args:
        diagram_type: 'mermaid' or 'svg'
        code: The diagram source code
        slug: Short kebab-case identifier (e.g. 'packet-flow')
    """
    res = VISUALS.publish_diagram(
        vault_dir=LOGGER.vault_dir,
        diagram_type=diagram_type,
        code=code,
        slug=slug
    )
    # Append to active log
    await LOGGER.append_diagram(diagram_type=diagram_type, code=code, title=slug)
    return res

def main():
    mcp.run()

if __name__ == "__main__":
    main()
