from collections import Counter
from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.config.CutConfig import CutConfig
from convert.adapters.solidworks.config.RootLayout import KConfigGen
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.resolved.BossEntry import ReadOpNode
from convert.adapters.solidworks.resolved.cut.CutChooser import KCutClass
from convert.adapters.solidworks.resolved.cut.CutEdgeRef import CheckCutEdges
from convert.adapters.solidworks.resolved.cut.CutLinks import CutLinks
from convert.adapters.solidworks.resolved.cut.CutOpRead import CutOperation, ReadCutOp
from convert.adapters.solidworks.resolved.cut.CutProfileBody import (
    CutProfileBody,
    ReadCutBody,
)
from convert.adapters.solidworks.resolved.cut.CutProfileSeal import (
    CutProfileSeal,
    ReadCutSeal,
)
from convert.adapters.solidworks.resolved.support.SupportPlane import (
    RequireFaceCap,
    ReadFaceSupport,
    SupportPlane,
)


# the cut proof binds the original profile and cap to a completely read operation
@Dataclass(frozen=True, slots=True)
class CutProof:
    Links: CutLinks
    Profile: CutProfileBody
    Support: SupportPlane
    SealValue: CutProfileSeal
    Operation: CutOperation


# the terminal cache uses two cut rings and one earlier boss ring in the same archive
def CheckCutSeal(
    Links: CutLinks,
    Profile: CutProfileBody,
    Support: SupportPlane,
    SealValue: CutProfileSeal,
) -> None:
    CapValue = Links.BossValue["choosers"]["caps"][1]
    RegionIds = set(Profile["chain"]["edge_ids"])
    EarlierIds = {EdgeValue["occurrence"] for EdgeValue in CapValue["edges"]}
    RequireArch(
        not bool(RegionIds & EarlierIds), True, "separate profile and boss contours"
    )
    RequireArch(
        Counter(EdgeValue["edge_id"] for EdgeValue in SealValue["trim_edges"]),
        Counter(
            {
                **{RegionId: 2 for RegionId in RegionIds},
                **{EdgeId: 1 for EdgeId in EarlierIds},
            }
        ),
        "cut trim cache retains both profile rings and the boss perimeter",
    )
    RequireArch(
        SealValue["placement"],
        Support["face"]["plane"]["transform"],
        "cut placement agrees with the saved face frame",
    )


# a cut is promoted only after the complete profile and operation reach the stream end
def ReadCutProof(Links: CutLinks, Config: CutConfig) -> CutProof:
    Cursor = Links.Cursor
    CutProfile = Links.CutProfile
    BossValue = Links.BossValue
    CapValue = BossValue["choosers"]["caps"][1]
    Profile = ReadCutBody(Cursor, CutProfile.SketchIndex)
    CheckCutEdges(Profile["edge_references"], CapValue)
    Support = ReadFaceSupport(Cursor, KConfigGen, 0)
    RequireFaceCap(Support, CapValue)
    FileObject = BossValue["file_ref_object"]
    SealValue = ReadCutSeal(
        Cursor,
        {
            "profile_object": CutProfile.ObjectIndex,
            "native_feature_id": CutProfile.FeatureId,
        },
        FileObject,
    )
    CheckCutSeal(Links, Profile, Support, SealValue)
    NodeValue = ReadOpNode(
        Cursor, KCutClass, (0x400201CA, 0xC00201CA), CutProfile.ObjectIndex, FileObject
    )
    Transfers = frozenset(
        Index
        for Index, ClassName in Config.Cursor.Objects.items()
        if ClassName == "moAtom_c"
    )
    Operation = ReadCutOp(Cursor, NodeValue, BossValue, Transfers)
    return CutProof(Links, Profile, Support, SealValue, Operation)
