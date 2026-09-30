import re
from typing import List, Tuple
from mcp_tutor.models import QuizRequest, QuizResult
from mcp_tutor.ui.web_modal import QUIZ_SERVER

def validate_distractor_quality(options: List[str]) -> List[str]:
    """
    Audits quiz options against Amos Blomqvist's distractor rules:
    1. Zero 'because' or justifications in options.
    2. No asymmetric bolding.
    3. Evenness of length and tone.
    """
    warnings = []
    
    # 1. Justification check
    justification_patterns = [r"\bbecause\b", r"\bsince\b", r"\bdue to\b", r"\bso that\b"]
    for i, opt in enumerate(options):
        for pat in justification_patterns:
            if re.search(pat, opt, re.IGNORECASE):
                warnings.append(
                    f"Option [{i+1}] contains justification ('{pat}'). "
                    "Options must be bare claims! Move all reasoning to 'explanation'."
                )

    # 2. Asymmetric bolding check
    bold_counts = [len(re.findall(r"\*\*.*?\*\*", opt)) for opt in options]
    if any(b > 0 for b in bold_counts) and not all(b == bold_counts[0] for b in bold_counts):
        warnings.append(
            "Asymmetric bolding detected across options. "
            "Highlighting only the correct answer flags it immediately. Bold nothing or bold all symmetrically."
        )

    return warnings

async def run_quiz(req: QuizRequest, auto_open: bool = True) -> Tuple[QuizResult, List[str]]:
    """
    Runs distractor validation and triggers the interactive quiz modal.
    Returns (QuizResult, warnings_list).
    """
    warnings = validate_distractor_quality(req.options)
    result = await QUIZ_SERVER.ask_quiz(req, auto_open=auto_open)
    return result, warnings
