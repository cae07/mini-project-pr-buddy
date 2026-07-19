from pathlib import Path

def write_report(
    summary: str,
    risks: list,
    recommendation: str
):
    report = f"""
# Review Report

## Summary
{summary}

## Risks

{chr(10).join(f"- {risk}" for risk in risks)}

## Recommendation

{recommendation}
"""

    Path("examples/review_report.md").write_text(
        report,
        encoding="utf-8"
    )

    return "examples/review_report.md"