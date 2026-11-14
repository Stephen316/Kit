from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


def AddNodeMut(
    Author: AuthorState,
    RoleName: str,
    ClassName: str,
    OwnerRole: str | None,
    HasStatus: bool = True,
) -> None:
    Author.Allocate(RoleName, ClassName, ParentRole="nodes")
    Author.Allocate(RoleName + "_dynamic", "DynamicUpdateData")
    Fields: dict[str, object] = dict(
        rDynamicUpdateData=Author.Reference(RoleName + "_dynamic"),
        rParentFeature=Author.Reference(OwnerRole),
    )
    if HasStatus:
        Author.Allocate(RoleName + "_status", "DcStatus", NamedPairs=[])
        Fields["status"] = Author.Reference(RoleName + "_status")
    Author.Change(RoleName, **Fields)
    Author.Change(
        RoleName + "_dynamic",
        rOwnerNode=Author.Reference(RoleName),
        timeStamp=Author.Policy.TimeStamp,
    )


def PartScope(Author: AuthorState) -> list[dict[str, object]]:
    return [
        Author.MakeGroup(
            "PassiveScopeValue",
            dict(
                assetId=Author.AssetId,
                scopeEntityIdentifier=Author.ComponentId,
                scopeIdType=2,
                segmentId=Author.Policy.DesignSegmentId,
            ),
        )
    ]
