# 🎓 `mcp-tutor`: Universal Active Learning & Socratic Tutoring MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Standard-purple.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Pedagogy: 3Blue1Brown](https://img.shields.io/badge/Pedagogy-3B1B%20Discovery-orange.svg)](https://www.youtube.com/watch?v=kzcI5F4tGiU)

> A portable, harness-agnostic **Model Context Protocol (MCP)** server that transforms any AI coding assistant into an exacting Socratic mentor, curriculum designer, and live visual note-taker.

Based on the pedagogy from Amos Blomqvist's viral system ([*“How I Use AI to Learn Things”*](https://www.youtube.com/watch?v=kzcI5F4tGiU)), generalized to run across **Antigravity**, **Claude Code**, **Cursor**, **Windsurf**, and any MCP-compliant environment.

---

## 🌟 Why `mcp-tutor`?

Standard LLM learning interactions suffer from **passive reading, sycophancy, rambling monologues, and unverified hallucinations**. You nod along to explanations, but the knowledge rots within days.

`mcp-tutor` enforces **active constructivist learning**:
1. **Unconditional Truths First**: Locks in solid, caveat-free foundational truths before building any derived abstractions.
2. **Motivated Discovery (3Blue1Brown Style)**: Never decrees arbitrary formulas; makes every concept feel naturally discovered to solve a concrete tension.
3. **Strict Socratic Gating**: The model cannot advance to the next concept without proving comprehension through an interactive diagnostic check.
4. **Live Obsidian Dual-Pane Sync**: Streams the lesson directly into an Obsidian vault with native LaTeX math (`$...$`) and diagram embeds, keeping answers hidden until submitted (**Delayed Reveal**).

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Client [Any MCP-Compliant AI Harness]
        Agent[AI Agent / LLM]
        Skill["Universal 'teach' Skill<br/>(skills/teach/SKILL.md)"]
        Agent --- Skill
    end

    subgraph MCPBridge [Model Context Protocol (stdio / JSON-RPC)]
        Agent -->|Tool Calls| Server[mcp-tutor Server]
        Server -->|Tool Results| Agent
    end

    subgraph Engines [Core Engines]
        QuizEngine["Quiz Engine<br/>• Bare-claim distractor check<br/>• Auto-injected 'I don't know'"]
        NoteEngine["Obsidian Live Sync<br/>• Delayed Answer Reveal<br/>• Native LaTeX Math ($...)"]
        VizEngine["Diagram Manager<br/>• Mermaid DAGs & SVGs<br/>• Saved to vault/viz/"]
    end

    subgraph Outputs [Learner Interface]
        UIModal["Interactive Micro-Modal<br/>(http://127.0.0.1:7331)<br/>Keys: 1-9, 0 (IDK), Enter"]
        VaultNote["Obsidian Markdown Note<br/>(notes/<topic>.md)"]
    end

    Server --> QuizEngine
    Server --> NoteEngine
    Server --> VizEngine

    QuizEngine --> UIModal
    NoteEngine --> VaultNote
    VizEngine --> VaultNote
```

---

## 🛠️ Tools Exposed to AI Agents

| Tool | Purpose | Key Mechanism |
| :--- | :--- | :--- |
| `pose_quiz` | Presents diagnostic multiple-choice questions. | Injects **"I don't know"** button, audits distractors against giveaway clues, triggers interactive UI popup. |
| `ask_learner` | Open-ended goal discovery and branching choices. | Clarifies vague learner intent into concrete milestones without right/wrong grading. |
| `init_session` | Starts a live lesson note in Obsidian. | Creates Markdown file with frontmatter metadata and prepares live stream. |
| `log_prose` | Streams lesson text and derivations. | Supports full LaTeX notation (`$f(x)$` and `$$...$$`). |
| `publish_diagram` | Generates Mermaid or SVG diagrams. | Publishes to `<vault>/viz/` with Obsidian wikilink embeds (`![[viz-slug.png|500]]`). |

---

## 🚀 Quickstart & Installation

### 1. Clone & Set Up Environment

```bash
git clone <YOUR_REPO_URL> mcp-tutor
cd mcp-tutor

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.venv\Scripts\activate
# Or on macOS/Linux:
# source .venv/bin/activate

# Install dependencies in editable mode
pip install -e .
```

### 2. Verify Installation
Run the included automated test suite:
```bash
python test_server.py
```
*(All distractor audits, delayed-reveal file writes, and diagram embeds should report `[PASS]`)*

---

## 🔌 Connecting to Your AI Client

### A. Antigravity IDE
Add the server to your Antigravity configuration (e.g., `~/.gemini/config/mcp_config.json` or `.agents/plugins/tutor/mcp_config.json`):

```json
{
  "mcpServers": {
    "tutor": {
      "command": "C:/path/to/mcp_tutor/.venv/Scripts/python.exe",
      "args": ["-m", "mcp_tutor.server"],
      "env": {
        "TUTOR_VAULT_DIR": "C:/path/to/your/notes",
        "TUTOR_WEB_PORT": "7331"
      }
    }
  }
}
```

### B. Claude Code
Register `mcp-tutor` with one command:
```bash
claude mcp add tutor -- /path/to/mcp_tutor/.venv/bin/python -m mcp_tutor.server
```

### C. Cursor
Navigate to **Settings > Features > MCP Servers > Add New MCP Server**:
* **Name**: `tutor`
* **Type**: `command`
* **Command**: `/path/to/mcp_tutor/.venv/bin/python -m mcp_tutor.server`

### D. Windsurf
Add to `~/.codeium/windsurf/mcp_config.json`:
```json
{
  "mcpServers": {
    "tutor": {
      "command": "/path/to/mcp_tutor/.venv/bin/python",
      "args": ["-m", "mcp_tutor.server"]
    }
  }
}
```

### E. Claude Desktop
Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "tutor": {
      "command": "python",
      "args": ["-m", "mcp_tutor.server"]
    }
  }
}
```

---

## 📖 How to Use the Teaching Skill

1. **Equip the Skill**: Copy [`skills/teach/SKILL.md`](skills/teach/SKILL.md) to your workspace's skill directory (e.g., `.agents/skills/teach/SKILL.md` or global skills).
2. **Prompt Your Agent**:
   > *"Teach me how the Self-Attention Mechanism works using the Socratic teach skill."*  
   > or  
   > *"Teach me the intuition behind the Fourier Transform from first principles."*
3. **Experience the 3-Phase Loop**:
   - **Phase 1 (Probe)**: The agent binary-searches your knowledge edge with quick quizzes and clarifies your operational goal.
   - **Phase 2 (Plan)**: It drafts a dependency DAG in Mermaid, stress-tests foundational roots, and waits for your confirmation.
   - **Phase 3 (Teach Loop)**: Walks through the DAG node by node: **Motivate $\rightarrow$ Establish $\rightarrow$ Connect $\rightarrow$ Quiz-Check**.
4. **Read Along in Obsidian**: Open the created note side-by-side with your chat. As you answer quizzes in the pop-up modal, the note updates in real time with derivations and LaTeX equations.

---

## 🎯 Distractor Quality Standards

`mcp-tutor` enforces strict quiz authoring rules inspired by psychometrics:
* **Zero Justifications in Options**: Options must be bare claims. Never write `"because X"`, `"since Y"`, or `"so that Z"`—all reasoning belongs in the `explanation` field to prevent giveaway length cues.
* **Parallel Register**: Every distractor must match the exact grammatical structure and grain size of the correct option.
* **The "I Don't Know" Guarantee**: Option `0` is always present. Honest admissions of gaps are celebrated and distinguished from lucky guesses.

---

## 🤝 Contributing

Contributions, bug reports, and pedagogical refinements are welcome! Feel free to open an issue or pull request.

---

## 📜 License

MIT License. See [LICENSE](LICENSE) for details.

### Acknowledgments
Inspired by **Amos Blomqvist**'s video [*“How I Use AI to Learn Things”*](https://www.youtube.com/watch?v=kzcI5F4tGiU) and **Grant Sanderson**'s ([3Blue1Brown](https://www.3blue1brown.com/)) motivated discovery philosophy.
