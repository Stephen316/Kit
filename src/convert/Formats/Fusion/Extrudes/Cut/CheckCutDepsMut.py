from convert.Formats.Fusion.Extrudes.Cut.CutEndData import CutEndData
from convert.Formats.Fusion.HistoryRef import ReadNativeRef
from convert.Formats.Fusion.MetaCursor import MetaCursor
from interchange.geometry.Models.Selection import Selection


# repeated dependencies must identify the target profile and the operands of the saved end code
def CheckCutDepsMut(
    Cursor: MetaCursor,
    Fields: CutEndData,
    Target: Selection,
    ProfileId: int,
    ProfileProxy: int,
    EndDescriptor: int | None,
) -> None:
    EndFields = (
        (Fields.AlongId,)
        if Fields.EndProxy is None
        else (Fields.EndProxy, EndDescriptor)
    )
    Expected = (
        Target.attributes.get("fusion.proxy_object_id"),
        Target.attributes.get("fusion.descriptor_object_id"),
        ProfileProxy,
        ProfileId,
        *EndFields,
        Fields.TaperId,
        Fields.CacheId,
    )
    Cursor.Offset = 249
    Count = Cursor.ReadCount(8)
    Observed = tuple(ReadNativeRef(Cursor) for _ in range(Count))
    if Observed != Expected or len(set(Observed)) != Count:
        raise ValueError("Fusion Cut control and repeated dependency records disagree")
