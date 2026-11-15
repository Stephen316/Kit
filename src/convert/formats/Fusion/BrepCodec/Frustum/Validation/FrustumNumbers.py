from math import isclose as IsClose, isfinite as IsFinite


# nonfinite coordinates and boolean numbers must fail before frustum geometry can enter native history
def CheckReal(Value: float) -> None:
    if isinstance(Value, bool) or not IsFinite(Value):
        raise ValueError("Frustum history requires finite real geometry")


# coedge orientation requires actual booleans so numeric values cannot silently change boundary direction
def CheckSense(Value: object) -> None:
    if type(Value) is not bool:
        raise ValueError("Frustum coedge senses must be Boolean")


# frustum frame vectors need three finite coordinates so downstream geometry cannot receive malformed axes
def CheckVector(Value: tuple[float, float, float]) -> None:
    if type(Value) is not tuple or len(Value) != 3:
        raise ValueError("Frustum history requires three-component vectors")
    for Member in Value:
        CheckReal(Member)


# reconstructed frustum values need tolerance comparisons because binary floating point cannot guarantee exact geometric equality
def IsNear(First: float, Second: float) -> bool:
    return IsClose(First, Second, rel_tol=1e-12, abs_tol=1e-10)


# frustum vectors need consistent component tolerances so equivalent frames survive floating point reconstruction
def IsNearVector(
    First: tuple[float, float, float], Second: tuple[float, float, float]
) -> bool:
    return all(
        IsNear(LeftValue, RightValue)
        for LeftValue, RightValue in zip(First, Second, strict=True)
    )
