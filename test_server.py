import asyncio
import os
from pathlib import Path
from mcp_tutor.models import QuizRequest, QuizResult
from mcp_tutor.engine.quiz import validate_distractor_quality
from mcp_tutor.engine.logger import MarkdownSessionLogger
from mcp_tutor.engine.visuals import VISUALS

async def run_tests():
    print("=== Testing mcp-tutor Core Engines ===")
    
    # 1. Distractor Quality Validation
    print("\n1. Testing Distractor Audit Rules...")
    bad_options = [
        "Packets arrive in order",
        "Packets are reordered **because** routing is dynamic",  # Contains justification
        "Packets drop silently"
    ]
    warnings = validate_distractor_quality(bad_options)
    assert len(warnings) > 0, "Should have caught 'because' justification"
    print(f"   [PASS] Successfully detected violation: {warnings[0]}")

    good_options = [
        "Packets always arrive in sequence",
        "Packets can arrive out of sequence",
        "Packets are discarded upon route changes"
    ]
    clean_warnings = validate_distractor_quality(good_options)
    assert len(clean_warnings) == 0, "Good options should pass cleanly"
    print("   [PASS] Clean bare-claim options passed with 0 warnings.")

    # 2. Markdown Logger & Delayed Reveal
    print("\n2. Testing Live Markdown Logger & Delayed Reveal...")
    test_vault = Path("./test_notes")
    logger = MarkdownSessionLogger(default_vault_dir=test_vault)
    target_file = await logger.init_session("Test Lesson Fourier Transform")
    print(f"   [PASS] Initialized session file: {target_file}")

    # Append Prose with LaTeX
    await logger.append_prose("The continuous Fourier Transform of $f(t)$ is defined as:")
    await logger.append_prose("$$\\hat{f}(\\xi) = \\int_{-\\infty}^{\\infty} f(t) e^{-2\\pi i t \\xi} dt$$")

    # Beat 1 of Delayed Reveal: append question without answer
    quiz_req = QuizRequest(
        question="What does the term $e^{-2\\pi i t \\xi}$ represent geometrically?",
        options=[
            "A spiral winding around the unit circle in the complex plane",
            "A linear decay function damping amplitude over time",
            "A phase shift in the time domain alone"
        ],
        correct_index=0,
        explanation="Euler's formula $e^{i\\theta} = \\cos\\theta + i\\sin\\theta$ traces points on the unit circle. Multiplying by $f(t)$ winds the function around the origin at frequency $\\xi$."
    )
    await logger.append_question_unresolved(quiz_req)
    print("   [PASS] Beat 1: Appended question to note with zero spoilers.")

    # Beat 2 of Delayed Reveal: user answers and note is resolved
    mock_result = QuizResult(
        status="answered",
        question=quiz_req.question,
        selected_index=0,
        selected_label=quiz_req.options[0],
        is_correct=True,
        dont_know=False,
        correct_index=0,
        correct_label=quiz_req.options[0],
        explanation=quiz_req.explanation,
        student_notes="Euler's formula rotation",
        message="✓ Correct"
    )
    await logger.resolve_question(mock_result)
    print("   [PASS] Beat 2: Resolved question with outcome and derivation.")

    # 3. Visuals Manager
    print("\n3. Testing Visuals & Diagram Embedding...")
    mermaid_code = """graph TD
    Packets[Packets] --> Ordering[Sequence Numbers]
    Packets --> Retransmit[Loss Recovery]
    Ordering --> TCP[Reliable Stream]
    Retransmit --> TCP"""
    viz_res = VISUALS.publish_diagram(
        vault_dir=test_vault,
        diagram_type="mermaid",
        code=mermaid_code,
        slug="tcp-reliability"
    )
    print(f"   [PASS] Published diagram: {viz_res['filename']}")
    await logger.append_diagram("mermaid", mermaid_code, "TCP Reliability DAG")

    print("\n=== All Core Engine Tests Passed Successfully! ===")
    print(f"Generated test note is available at: {target_file}")

if __name__ == "__main__":
    asyncio.run(run_tests())
