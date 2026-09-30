import os
from pathlib import Path
from pydantic import BaseModel, Field

class TutorConfig(BaseModel):
    vault_dir: Path = Field(
        default_factory=lambda: Path(os.environ.get("TUTOR_VAULT_DIR", Path.cwd() / "notes")),
        description="Path to the Obsidian vault or markdown notes directory"
    )
    ui_mode: str = Field(
        default=os.environ.get("TUTOR_UI_MODE", "auto"),
        description="Interaction UI mode: 'auto', 'web', 'gui', or 'cli'"
    )
    web_port: int = Field(
        default=int(os.environ.get("TUTOR_WEB_PORT", 7331)),
        description="Local web modal port for quiz and question prompts"
    )
    auto_open_browser: bool = Field(
        default=True,
        description="Automatically open the interactive web modal when a quiz is posed"
    )

# Global default config instance
CONFIG = TutorConfig()
