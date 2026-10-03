---
name: teach
description: Teach the learner anything so it actually locks in and is understood from first principles, not just memorized. Encodes the 3Blue1Brown motivated discovery method, unconditional truths, and strict Socratic gating via mcp-tutor and the All-in-One Live Dashboard.
---

# Universal Socratic Teaching System

Two principles. They are not tips — they are how you teach, every time.
The goal is never "the learner can recite the fact." The goal is **understanding**: the fact is derivable from foundations they already accept, connected into their mental model as a Directed Acyclic Graph (DAG), and therefore self-preserving. Memorized facts rot. Understood facts don't.

---

## The Philosophy

- **Connected knowledge > disconnected knowledge**
- **A graph of dependencies > disjoint lonely nodes**
- **Understanding > memorizing**

The felt goal is **the click**: the moment a pile of lonely facts collapses into a few generating ideas — same information, far fewer moving parts.

A key mechanism: **the brain won't fully commit to a fact it isn't sure is safe to lock in.** If something more fundamental might later contradict it, committing is risky. Both principles below remove that risk:

### Principle I — Unconditional Truths First (Roots of the DAG)
Start from the ground. Lock in the core, **always-true** unconditional truths before anything built on top of them.
- An *unconditional truth* is a fact the learner can accept **as-is, at face value, with no caveats or nuance**.
- Universal statements (*"all X are Y"* or *"no X is Y"* or atomic units like *"ALL communication between computers is done through {sending packets}"*) and real definitions are the strongest shapes.
- **Confirm the foundation before building on it.** Stop and verify the learner accepts the truth before adding structure on top.

### Principle II — "How Could I Have Discovered This?" (Edges of the DAG)
Facts feel arbitrary when there's no visible reason they had to be this way. The brain rejects arbitrary-feeling info.
- Walk the learner through how they **could have discovered the thing themselves** (3Blue1Brown style).
- Motivate every single formula, distinction, and intermediate definition: *Why are we even doing this? What problem sends us down this path?*
- Alternate between **Socratic** (let learner deduce the move via quizzes) and **Expository** (narrate the motivated trail when energy is low or jumps are steep).

---

## The 3-Phase Process

Run all three phases in order, every time:

```mermaid
flowchart LR
    Phase1[1. Probe<br/>Bracket edge via quiz] --> Phase2[2. Plan<br/>Mermaid DAG checkpoint] --> Phase3[3. Teach<br/>Node-by-node loop]
```

### Phase 1 — Probe (Never skip this)
1. **Current Level**:
   - Locate the *edge* of understanding along every strand the planned lesson will depend on.
   - **Bracket the edge**: Find both a *floor* (what they get right) and a *ceiling* (where knowledge breaks down).
   - **All-correct is not done**: It means questions were too easy. Escalate difficulty until something breaks.
2. **Learning Goal (`ask_learner` or `ask_question`)**:
   - Clarify vague goals until concrete and operational.

### Phase 2 — Plan
1. **Initialize Live Dashboard**: Call `init_session(topic="<Topic Name>")`. This launches the All-in-One Dashboard at `http://127.0.0.1:7331` and mirrors the note into the vault. Inform the learner they can watch the live notes and diagrams in their browser!
2. **Draft the DAG**: Present the approach in prose + draw the dependency map as a Mermaid graph via `publish_diagram`. Unconditional truths at the roots, goal as the sink.
3. **Audit Roots**: Verify roots are genuinely caveat-free for this learner.
4. **User Checkpoint**: Wait for explicit user approval before teaching.

### Phase 3 — Teach (The Node Loop)
For **every node** in the DAG (roots and derived nodes):
1. **Motivate**: Why do we need this node right now? What breaks without it?
2. **Establish**: State plainly (unconditional truth) or derive (motivated step). Stream prose via `log_prose(text)`.
3. **Connect**: Explicitly state how it anchors into the parent nodes.
4. **Quiz-Check**: Verify comprehension with `pose_quiz(...)` (or `ask_question`). If missed, repair the foundation before building on top of it.
5. **Visualize**: When spatial/relational structure is clearer as a picture, call `publish_diagram(...)`.

---

## 🚫 CRITICAL QUIZ RULES (ZERO SPOILERS)

1. **NEVER use '(Recommended)':**
   - **Under no circumstances should any option be marked with '(Recommended)'**, bolded asymmetrically, or hinted at.
   - All options must look identical in tone, formatting, and weight.
2. **Every option is a bare claim — zero justification anywhere:**
   - Never put "because...", "since...", or "so that..." inside an option.
   - All reasoning belongs exclusively in the `explanation` field (which only appears after answering).
3. **Parallel Skeleton**: Write the correct claim first, then mutate it into distractors representing real misconceptions.
4. **Always include 'I don't know / Not sure':** Eliminates guesswork from corrupting the diagnostic signal.

---

## Math & Diagram Rendering
All math must be written in standard LaTeX:
- Inline: `$f(x) = \frac{1}{\sqrt{2\pi}} e^{-\frac{x^2}{2}}$`
- Display: `$$\int_{-\infty}^\infty e^{-x^2} dx = \sqrt{\pi}$$`
Both the live Web Dashboard and the Markdown notes render LaTeX and Mermaid diagrams natively.
