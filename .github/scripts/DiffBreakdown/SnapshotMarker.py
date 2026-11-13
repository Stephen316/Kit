from __future__ import annotations

import base64 as BaseCodec
import json as JsonLib

KMarkerOpen = "<!-- kit-diff-breakdown:v1:"
KMarkerClose = " -->"
KOmittedKeys = frozenset({"Files", "PushFiles", "CommentId"})


def BuildMarker(Snapshot: dict[str, object]) -> str:
    Compact = {
        KeyText: Value
        for KeyText, Value in Snapshot.items()
        if KeyText not in KOmittedKeys
    }
    JsonText = JsonLib.dumps(Compact, separators=(",", ":"), ensure_ascii=True)
    return (
        f"{KMarkerOpen}{BaseCodec.b64encode(JsonText.encode()).decode()}{KMarkerClose}"
    )


def DecodeMarker(BodyText: str) -> dict[str, object] | None:
    StartIndex = BodyText.find(KMarkerOpen)
    if StartIndex < 0:
        return None
    StartIndex += len(KMarkerOpen)
    EndIndex = BodyText.find(KMarkerClose, StartIndex)
    if EndIndex < 0:
        return None
    try:
        Record = JsonLib.loads(
            BaseCodec.b64decode(BodyText[StartIndex:EndIndex], validate=True)
        )
    except ValueError:
        return None
    return Record if isinstance(Record, dict) else None
