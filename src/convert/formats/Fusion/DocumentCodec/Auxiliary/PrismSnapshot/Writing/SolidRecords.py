from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
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
from convert.formats.Fusion.GeometryCodec.CylinderRoots import BuildRoots
from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.Prism.PrismPoints import BuildPoints


def SolidRecords(Frame: PrismFrame) -> tuple[GeometryRecord, ...]:
    Records = (
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
    Shell = Records[3]
    Shell = ReplaceValue(
        Shell,
        Fields=(
            *Shell.Fields[:5],
            EntityRef(4 + Frame.FaceOrder[0]),
            *Shell.Fields[6:],
        ),
    )
    return (*Records[:3], Shell, *Records[4:])
