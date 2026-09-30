from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# Constants matching Amos's pedagogy
DONT_KNOW_VALUE = "__dont_know__"
DONT_KNOW_LABEL = "I don't know / Not sure"

class QuizOption(BaseModel):
    label: str
    value: str
    is_dont_know: bool = False

class QuizRequest(BaseModel):
    question: str = Field(description="The diagnostic question to present")
    options: List[str] = Field(description="Bare-claim answer choices. Put ZERO explanations in options.")
    correct_index: int = Field(description="0-based index of the correct option")
    explanation: str = Field(description="Detailed derivation and explanation, shown ONLY after answering")
    context: Optional[str] = Field(default=None, description="Optional lead-in scenario or motivation")
    mode: Literal["single-select", "multi-select"] = "single-select"

class QuizResult(BaseModel):
    status: Literal["answered", "cancelled", "unavailable"] = "answered"
    question: str
    selected_index: int = Field(description="0-based index of the option chosen by user (-1 if I don't know)")
    selected_label: str
    is_correct: bool
    dont_know: bool
    correct_index: int
    correct_label: str
    explanation: str
    student_notes: Optional[str] = None
    message: str

class AskRequest(BaseModel):
    prompt: str = Field(description="The open-ended question, goal clarification, or preference prompt")
    options: Optional[List[str]] = Field(default=None, description="Optional list of choices for branching")
    mode: Literal["free-text", "single-select", "multi-select"] = "free-text"

class AskResult(BaseModel):
    status: Literal["answered", "cancelled", "unavailable"] = "answered"
    prompt: str
    answers: List[str]
    notes: Optional[str] = None

class LogAction(BaseModel):
    file_path: Optional[str] = None
    topic: Optional[str] = None
    action: Literal["init", "append_prose", "append_question", "resolve_question", "append_diagram"]
    content: Optional[str] = None
    question: Optional[QuizRequest] = None
    result: Optional[QuizResult] = None
