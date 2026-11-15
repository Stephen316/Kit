import hashlib as Hashing
import json as JsonCodec


# lease fingerprint comparisons require a stable encoding across controller process invocations
def HashText(Value: object) -> str:
    return Hashing.sha256(
        JsonCodec.dumps(Value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
