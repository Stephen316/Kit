from collections.abc import Mapping
from typing import cast as CastValue


# native version needs an explicit validity boundary so public document claims remain grounded in native records
def NativeVersion(Value: object) -> int:
    if not isinstance(Value, Mapping):
        raise ValueError("Native Fusion state requires a versioned mapping")
    Version = CastValue(Mapping[str, object], Value).get("version")
    if type(Version) is not int or Version not in (1, 2):
        raise ValueError("Unsupported native Fusion state version")
    return Version
