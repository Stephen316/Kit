import json
import re

from Records import canonical

FRAME_LIMIT = 8192
CLAIM_NAME = re.compile(r"[a-f0-9]+-[a-f0-9]{8}\.json")


class ClaimExchangeLost(ValueError):
    pass


def send_frame(stream, record):
    data = (canonical(record) + "\n").encode("utf-8")
    if len(data) > FRAME_LIMIT or stream.write(data) != len(data):
        raise OSError("claim helper could not write a complete frame")
    stream.flush()


def read_frame(stream):
    data = stream.readline(FRAME_LIMIT + 1)
    if not data:
        return None
    if len(data) > FRAME_LIMIT or not data.endswith(b"\n"):
        raise ValueError("claim helper frame is oversized or incomplete")
    result = json.loads(data)
    if not isinstance(result, dict):
        raise ValueError("claim helper message must be an object")
    return result
