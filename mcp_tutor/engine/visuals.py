import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

class VisualManager:
    def __init__(self, viz_dir_name: str = "viz"):
        self.viz_dir_name = viz_dir_name

    def publish_diagram(self, vault_dir: Path, diagram_type: str, code: str, slug: str) -> Dict[str, Any]:
        """
        Publishes a diagram (Mermaid or SVG) into the vault's viz directory
        and returns the markdown embed string for Obsidian.
        """
        viz_dir = vault_dir / self.viz_dir_name
        viz_dir.mkdir(parents=True, exist_ok=True)

        timestamp = int(time.time())
        ext = "mmd" if diagram_type == "mermaid" else "svg"
        filename = f"viz-{slug}-{timestamp}.{ext}"
        filepath = viz_dir / filename

        # Write the source
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code.strip())

        # Obsidian embeds
        if diagram_type == "mermaid":
            # Obsidian renders raw mermaid blocks natively
            embed_text = f"```mermaid\n{code.strip()}\n```"
        else:
            # SVG can be embedded via wikilink
            embed_text = f"![[{filename}|500]]"

        return {
            "status": "published",
            "filename": filename,
            "filepath": str(filepath),
            "embed": embed_text
        }

VISUALS = VisualManager()
