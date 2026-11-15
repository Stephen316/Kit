from typing import cast as CastValue

from interchange.geometry.models.Sketch import SketchEntity


# native endpoint identities distinguish a saved line from coincident point copies
def ReadLineEnds(Entity: SketchEntity) -> tuple[int, int]:
    PointIds = Entity.attributes.get("fusion.line_native_point_ids")
    if not isinstance(PointIds, tuple):
        raise ValueError("Fusion line endpoints are unbound")
    Values = CastValue(tuple[object, ...], PointIds)
    if len(Values) != 2:
        raise ValueError("Fusion line has an invalid endpoint count")
    Start, Finish = Values
    if type(Start) is not int or type(Finish) is not int or Start == Finish:
        raise ValueError("Fusion line endpoint identities are ambiguous")
    return Start, Finish
