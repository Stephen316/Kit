from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismTags import PrismTags
from convert.formats.Fusion.BrepCodec.Prism.PrismLayout import (
    KFirstAttribute,
    KFirstFaceTag,
    KFirstSketchTag,
    KSketchOwners,
)
from convert.formats.Fusion.BrepCodec.Prism.Writing.PrismAttrs import PrismAttrs
from convert.formats.Fusion.BrepCodec.Prism.Writing.PrismCarriers import (
    PrismCurves,
    PrismPlanes,
)
from convert.formats.Fusion.BrepCodec.Prism.Writing.PrismCoedges import PrismCoedges
from convert.formats.Fusion.BrepCodec.Prism.Writing.PrismEdges import PrismEdges
from convert.formats.Fusion.BrepCodec.Prism.Writing.PrismFaces import (
    PrismFaces,
    PrismLoops,
)
from convert.formats.Fusion.BrepCodec.Prism.Writing.PrismVertices import PrismVertices
from convert.formats.Fusion.BrepCodec.Topology.AssignHeads import AssignHeads
from convert.formats.Fusion.GeometryCodec.CylinderRoots import BuildRoots
from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import KFirstFace
from convert.formats.Fusion.GeometryCodec.Prism.PrismPoints import BuildPoints


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
