from math import isfinite as IsFinite
from struct import pack as PackValue


def EncodeFloat(Value: float) -> bytes:
    if type(Value) not in (int, float):
        raise ValueError("Fusion material scalar must be finite")
    try:
        Numeric = float(Value)
    except OverflowError:
        raise ValueError("Fusion material scalar exceeds binary64 range") from None
    if not IsFinite(Numeric):
        raise ValueError("Fusion material scalar must be finite")
    return PackValue("<d", Numeric)
