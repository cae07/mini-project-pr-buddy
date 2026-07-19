from typing import TypedDict

class PRReviewState(TypedDict):
    file_path: str
    diff_content: str

    summary: str
    risks: list[str]

    recommendation: str

    report_path: str
