
# the axis source id contract needs a shared interpretation so stream contents retain their geometry and feature relationships
def AxisSourceId(KindValue: str, NativeId: int) -> str:
    return f"sldprt:{KindValue}:{NativeId}"


# the marker id contract needs a shared interpretation so stream contents retain their geometry and feature relationships
def MarkerId(NativeId: int, Offset: int) -> str:
    return f"sldprt:sketch:{NativeId}:native:{Offset}"
