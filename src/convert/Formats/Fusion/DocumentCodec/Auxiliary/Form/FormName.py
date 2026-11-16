from uuid import UUID as UuidValue

from convert.Formats.Fusion.DocumentCodec.Auxiliary.Form.FormLayout import KFormFolder


# form name needs an explicit validity boundary so supporting records retain their owning document relationships
def FormName(Value: str) -> str:
    Prefix = KFormFolder + "TSpline."
    if not Value.startswith(Prefix) or not Value.endswith(".tsm"):
        raise ValueError("Unsupported document T-spline part name")
    Identity = Value[len(Prefix) : -len(".tsm")]
    if str(UuidValue(Identity)).lower() != Identity.lower():
        raise ValueError("Invalid document T-spline part UUID")
    return Value.removeprefix(KFormFolder)
