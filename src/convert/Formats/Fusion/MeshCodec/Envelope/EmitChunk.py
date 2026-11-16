# the chunk operation needs a consistent construction rule so vertex and index streams retain their intended connectivity
def EmitChunk(Payload: bytes, KindValue: int) -> bytes:
    if len(Payload) > 64 * 1024 * 1024:
        raise ValueError("Fusion mesh chunk allocation exceeds limit")
    return (
        len(Payload).to_bytes(8, "little") + KindValue.to_bytes(4, "little") + Payload
    )
