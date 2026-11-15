import json as JsonCodec
import os as OsLayer
import sys as System
from pathlib import Path as FilePath


def WriteNoise() -> None:
    SessionPath = FilePath(System.argv[1])
    for StreamId in (1, 2):
        Content = b"x" * 2097152
        while Content:
            Content = Content[OsLayer.write(StreamId, Content) :]
    ResultInfo: dict[str, object] = {
        "outcome": "completed",
        "reason": "noise finished",
        "records": {"count": 1, "inputs": [], "tokenless": True},
    }
    _ = (SessionPath / "result.json").write_text(
        JsonCodec.dumps(ResultInfo), encoding="utf-8"
    )


if __name__ == "__main__":
    WriteNoise()
