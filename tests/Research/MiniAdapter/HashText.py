import hashlib as Hashing
import json as JsonCodec


def HashText(Value: object) -> str:
    return Hashing.sha256(
        JsonCodec.dumps(Value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
