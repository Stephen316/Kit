from collections.abc import Callable
from convert.formats.Fusion.BrepCodec.Journal.Reading.Attributes.ReadNoMerge import (
    ReadNoMerge,
)
from convert.formats.Fusion.BrepCodec.Journal.Round.ReadSphereNode import ReadSphereNode
from convert.formats.Fusion.BrepCodec.Journal.Round.ReadTorusNode import ReadTorusNode

from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadIntcurve import (
    ReadIntcurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadPcurveNode import (
    ReadPcurveNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadSplineNode import (
    ReadSplineNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Reading.ReadTcoedgeNode import (
    ReadTcoedgeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Reading.ReadTedgeNode import (
    ReadTedgeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Reading.ReadTvertexNode import (
    ReadTvertexNode,
)
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Attributes.ReadAttribNode import (
    ReadAttribNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Attributes.ReadSysAttrib import (
    ReadStitchNode,
    ReadVertedge,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Attributes.ReadGenAttrib import (
    ReadLongName,
    ReadNameNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadWireNode import (
    ReadWireNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadAsmRoot import (
    ReadAsmRoot,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadBodyNode import (
    ReadBodyNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadLumpNode import (
    ReadLumpNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadShellNode import (
    ReadShellNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadFaceNode import (
    ReadFaceNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadLoopNode import (
    ReadLoopNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadCoedgeNode import (
    ReadCoedgeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadEdgeNode import (
    ReadEdgeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadVertexNode import (
    ReadVertexNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadPointNode import (
    ReadPointNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadPlaneNode import (
    ReadPlaneNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadEllipseNode import (
    ReadEllipseNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadConeNode import (
    ReadConeNode,
)

from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadStraight import (
    ReadStraight,
)

from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadTransform import (
    ReadTransform,
)

KEntityReaders: dict[str, Callable[[FieldCursor], KJournalEntity]] = {
    "spline-surface": ReadSplineNode,
    "intcurve-curve": ReadIntcurve,
    "pcurve": ReadPcurveNode,
    "tcoedge-coedge": ReadTcoedgeNode,
    "tedge-edge": ReadTedgeNode,
    "tvertex-vertex": ReadTvertexNode,
    "sphere-surface": ReadSphereNode,
    "torus-surface": ReadTorusNode,
    "straight-curve": ReadStraight,
    "transform": ReadTransform,
    "asmheader": ReadAsmRoot,
    "body": ReadBodyNode,
    "lump": ReadLumpNode,
    "shell": ReadShellNode,
    "wire": ReadWireNode,
    "face": ReadFaceNode,
    "loop": ReadLoopNode,
    "coedge": ReadCoedgeNode,
    "edge": ReadEdgeNode,
    "vertex": ReadVertexNode,
    "point": ReadPointNode,
    "plane-surface": ReadPlaneNode,
    "ellipse-curve": ReadEllipseNode,
    "cone-surface": ReadConeNode,
    "ATTRIB_CUSTOM-attrib": ReadAttribNode,
    "stitch_hint-sys-attrib": ReadStitchNode,
    "no_merge_attribute-st-attrib": ReadNoMerge,
    "vertedge-sys-attrib": ReadVertedge,
    "name_attrib-gen-attrib": ReadNameNode,
    "int64_attrib-name_attrib-gen-attrib": ReadLongName,
}
