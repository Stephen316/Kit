from datetime import datetime as DateTime


def CheckTimestamp(Value: str) -> None:
    try:
        Parsed = DateTime.fromisoformat(Value.replace("Z", "+00:00"))
    except (ValueError, TypeError) as ErrorInfo:
        raise ValueError("Invalid material timestamp") from ErrorInfo
    if Parsed.tzinfo is None or len(Value) > 64:
        raise ValueError(
            "Material timestamp requires a bounded timezone-qualified value"
        )
