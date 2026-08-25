from typing import TypedDict

class PRReviewState(TypedDict):
    file_path: str
    diff_content: str

    security_summary: str
    security_risks: list[str]

    quality_summary: str
    quality_risks: list[str]

    summary: str
    risks: list[str]

    recommendation: str
    flow_status: str

    report_path: str