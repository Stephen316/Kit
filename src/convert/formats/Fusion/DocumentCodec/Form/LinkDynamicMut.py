from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


def LinkDynamicMut(Author: AuthorState, UnixMicros: int) -> None:
    Reference = Author.Reference
    Stamps = {
        "dc_component": UnixMicros - 2,
        "form_tool": UnixMicros - 1,
        "form_feature": UnixMicros,
        "form_data": UnixMicros + 1,
    }
    Author.Change("dynamic", timeStamp=Stamps["dc_component"])
    Sources = {
        "form_feature": ("dc_component", "form_feature", "form_tool"),
        "form_tool": ("form_tool",),
        "form_data": (),
    }
    for RoleName, Owners in Sources.items():
        Author.Change(RoleName, rDynamicUpdateData=Reference(RoleName + "_dynamic"))
        Author.Change(
            RoleName + "_dynamic",
            isBodyOK=bool(Owners),
            isPredecessorOK=bool(Owners),
            predecessors=[
                {"key": Reference(OwnerName), "value": Stamps[OwnerName]}
                for OwnerName in Owners
            ],
            rOwnerNode=Reference(RoleName),
            timeStamp=Stamps[RoleName],
        )
