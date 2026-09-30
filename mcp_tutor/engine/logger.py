import asyncio
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import aiofiles
from mcp_tutor.models import QuizRequest, QuizResult

class MarkdownSessionLogger:
    def __init__(self, default_vault_dir: Path):
        self.vault_dir = default_vault_dir
        self.active_file: Optional[Path] = None
        self._lock = asyncio.Lock()

    def set_active_file(self, file_path_or_topic: str) -> Path:
        p = Path(file_path_or_topic)
        if not p.is_absolute():
            # If relative, place inside vault_dir
            if not p.suffix:
                # Given topic name e.g. "fourier_transform"
                safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in file_path_or_topic)
                p = self.vault_dir / f"{safe_name}.md"
            else:
                p = self.vault_dir / p
        
        p.parent.mkdir(parents=True, exist_ok=True)
        self.active_file = p
        return p

    async def init_session(self, topic: str, file_path: Optional[str] = None) -> str:
        target = self.set_active_file(file_path or topic)
        async with self._lock:
            if not target.exists():
                header = (
                    f"---\n"
                    f"title: \"{topic}\"\n"
                    f"created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"type: tutor-lesson\n"
                    f"---\n\n"
                    f"# Learning: {topic}\n\n"
                )
                async with aiofiles.open(target, "w", encoding="utf-8") as f:
                    await f.write(header)
        return str(target)

    async def append_prose(self, prose: str) -> None:
        if not self.active_file:
            return
        async with self._lock:
            async with aiofiles.open(self.active_file, "a", encoding="utf-8") as f:
                await f.write(f"\n{prose.strip()}\n\n")

    async def append_diagram(self, diagram_type: str, code: str, title: Optional[str] = None) -> None:
        if not self.active_file:
            return
        async with self._lock:
            block = f"\n```{diagram_type}\n{code.strip()}\n```\n\n"
            if title:
                block = f"### {title}\n" + block
            async with aiofiles.open(self.active_file, "a", encoding="utf-8") as f:
                await f.write(block)

    async def append_question_unresolved(self, req: QuizRequest) -> None:
        """
        Delayed Reveal Beat 1: Appends the question with blank checkboxes.
        Zero answers or explanations are written yet to prevent spoilers!
        """
        if not self.active_file:
            return
        async with self._lock:
            lines = [
                f"\n> [!QUESTION] **Diagnostic Question**",
                f"> {req.question}",
            ]
            if req.context:
                lines.insert(1, f"> *Context: {req.context}*")
            lines.append(">")
            for i, opt in enumerate(req.options):
                lines.append(f"> - [ ] **({i+1})** {opt}")
            lines.append(f"> - [ ] **(0)** I don't know / Not sure")
            lines.append("\n")

            async with aiofiles.open(self.active_file, "a", encoding="utf-8") as f:
                await f.write("\n".join(lines))

    async def resolve_question(self, res: QuizResult) -> None:
        """
        Delayed Reveal Beat 2: Appends the student's answer, correctness, and explanation.
        """
        if not self.active_file:
            return
        async with self._lock:
            icon = "✓" if res.is_correct else ("❓" if res.dont_know else "✗")
            title = "Correct" if res.is_correct else ("I Don't Know" if res.dont_know else "Misconception")
            
            lines = [
                f"> [!NOTE] **Outcome: {icon} {title}**",
                f"> - **Learner Selection:** {res.selected_label}",
                f"> - **Ground Truth:** {res.correct_label}",
            ]
            if res.student_notes:
                lines.append(f"> - **Learner Note:** *\"{res.student_notes}\"*")
            lines.append(">")
            lines.append(f"> **Explanation / Derivation:**")
            for exp_line in res.explanation.splitlines():
                lines.append(f"> {exp_line}")
            lines.append("\n")

            async with aiofiles.open(self.active_file, "a", encoding="utf-8") as f:
                await f.write("\n".join(lines))

# Global session logger instance
LOGGER = MarkdownSessionLogger(default_vault_dir=Path.cwd() / "notes")
