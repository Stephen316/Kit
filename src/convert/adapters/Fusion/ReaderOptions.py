from collections.abc import Callable, Mapping
from typing import cast as CastValue

from convert.adapters.base.ReadOptions import ReadOptions

# source object identities occupy one unsigned field in the native history table
KMaxHistoryId = (1 << 64) - 1


# adapter options keep incomplete coverage and native history selection explicit
def GetFusionOpts(
    Options: ReadOptions,
) -> tuple[int | None, Callable[[bytes, int], bytes] | None]:
    if Options.strict is not False:
        raise ValueError("Fusion F3D reading is partial. Pass strict=False to opt in.")
    if not isinstance(CastValue(object, Options.values), Mapping):
        raise TypeError("Fusion read option values must be a mapping")
    ConfigId = None
    ConfigText = CastValue(object, Options.configuration)
    if ConfigText is not None:
        if (
            not isinstance(ConfigText, str)
            or not 1 <= len(ConfigText) <= 20
            or not ConfigText.isascii()
            or not ConfigText.isdecimal()
            or not 1 <= int(ConfigText) <= KMaxHistoryId
        ):
            raise ValueError(
                "Fusion configuration must be a positive decimal native history ID"
            )
        ConfigId = int(ConfigText)
    HistoryId = ConfigId
    if "fusion.history_id" in Options.values:
        NativeId = Options.values["fusion.history_id"]
        if type(NativeId) is not int or not 1 <= NativeId <= KMaxHistoryId:
            raise ValueError(
                "fusion.history_id must be a positive integer native history ID"
            )
        HistoryId = NativeId
    if ConfigId is not None and ConfigId != HistoryId:
        raise ValueError("Fusion configuration and fusion.history_id disagree")
    if "fusion.inflate_zstd" not in Options.values:
        return HistoryId, None
    Inflate = Options.values["fusion.inflate_zstd"]
    if not callable(Inflate):
        raise ValueError("fusion.inflate_zstd must be callable")
    return HistoryId, CastValue(Callable[[bytes, int], bytes], Inflate)
