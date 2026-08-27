from typing import TypedDict


class PRReviewState(TypedDict):

    trace_id: str
    started_at: str
    file_path: str
    diff_content: str

    review_history: list

    security_summary: str
    security_risks: list[str]

    quality_summary: str
    quality_risks: list[str]

    summary: str
    risks: list[str]

    recommendation: str
    flow_status: str

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    report_path: str