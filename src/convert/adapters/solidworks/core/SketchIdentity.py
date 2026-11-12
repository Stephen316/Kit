
def AxisSourceId(KindValue: str, NativeId: int) -> str:
    return f"sldprt:{KindValue}:{NativeId}"


def MarkerId(NativeId: int, Offset: int) -> str:
    return f"sldprt:sketch:{NativeId}:native:{Offset}"
