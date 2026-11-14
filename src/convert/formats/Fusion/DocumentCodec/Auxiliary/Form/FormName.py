from uuid import UUID as UuidValue

from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.FormLayout import KFormFolder


def FormName(Value: str) -> str:
    Prefix = KFormFolder + "TSpline."
    if not Value.startswith(Prefix) or not Value.endswith(".tsm"):
        raise ValueError("Unsupported document T-spline part name")
    Identity = Value[len(Prefix) : -len(".tsm")]
    if str(UuidValue(Identity)).lower() != Identity.lower():
        raise ValueError("Invalid document T-spline part UUID")
    return Value.removeprefix(KFormFolder)
