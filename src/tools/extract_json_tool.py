import re


def extract_json(raw_content):
    cleaned_content = re.sub(
        r"^```json\s*|\s*```$",
        "",
        raw_content,
        flags=re.IGNORECASE | re.MULTILINE
    ).strip()

    return cleaned_content