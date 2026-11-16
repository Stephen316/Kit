from dataclasses import replace as ReplaceValue

from convert.Formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismTags import PrismTags
from convert.Formats.Fusion.BrepCodec.Prism.PrismLayout import (
    KFirstAttribute,
    KFirstFaceTag,
    KFirstSketchTag,
    KSketchOwners,
)
from convert.Formats.Fusion.BrepCodec.Prism.Writing.PrismAttrs import PrismAttrs
from convert.Formats.Fusion.BrepCodec.Prism.Writing.PrismCarriers import (
    PrismCurves,
    PrismPlanes,
)
from convert.Formats.Fusion.BrepCodec.Prism.Writing.PrismCoedges import PrismCoedges
from convert.Formats.Fusion.BrepCodec.Prism.Writing.PrismEdges import PrismEdges
from convert.Formats.Fusion.BrepCodec.Prism.Writing.PrismFaces import (
    PrismFaces,
    PrismLoops,
)
from convert.Formats.Fusion.BrepCodec.Prism.Writing.PrismVertices import PrismVertices
from convert.Formats.Fusion.BrepCodec.Topology.AssignHeads import AssignHeads
from convert.Formats.Fusion.GeometryCodec.CylinderRoots import BuildRoots
from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.Prism.PrismLayout import KFirstFace
from convert.Formats.Fusion.GeometryCodec.Prism.PrismPoints import BuildPoints


# the prism records contract needs a shared interpretation so profile topology remains connected to its extrusion history
def PrismRecords(
    Identity: BodyIdentity, TagSet: PrismTags, Frame: PrismFrame
) -> tuple[GeometryRecord, ...]:
    Records = list(
        (
            *BuildRoots(),
            *PrismFaces(Frame),
            *PrismLoops(Frame),
            *PrismCoedges(Frame),
            *PrismEdges(Frame),
            *PrismPlanes(Frame),
            *PrismVertices(Frame),
            *PrismCurves(Frame),
            *BuildPoints(Frame.CornersCm),
        )
    )
    BodyValue, Shell = Records[1], Records[3]
    Records[1] = ReplaceValue(
        BodyValue, Fields=(BodyValue.Fields[0], Identity.BodyKey, *BodyValue.Fields[2:])
    )
    Records[3] = ReplaceValue(
        Shell,
        Fields=(
            *Shell.Fields[:5],
            EntityRef(KFirstFace + Frame.FaceOrder[0]),
            *Shell.Fields[6:],
        ),
    )
    Heads = (
        (1, KFirstAttribute),
        *((KFirstFace + Index, KFirstFaceTag + Index) for Index in range(6)),
        *(
            (Owner, KFirstSketchTag + 2 * Index + Offset)
            for Index, Owners in enumerate(KSketchOwners)
            for Offset, Owner in enumerate(Owners)
        ),
    )
    return (*AssignHeads(tuple(Records), Heads), *PrismAttrs(Identity, TagSet))
