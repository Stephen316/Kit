from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import (
    PrismSnapshot,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionEdge import (
    RegionEdge,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionFrame import (
    RegionFrame,
)
from convert.Formats.Fusion.DocumentCodec.Materials.Model.DirectionValue import (
    DirectionValue,
)
from convert.Formats.Fusion.DocumentCodec.Materials.Model.FinishSpec import FinishSpec
from convert.Formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.Formats.Fusion.DocumentCodec.Materials.Model.MechanicSpec import (
    MechanicSpec,
)
from convert.Formats.Fusion.DocumentCodec.Materials.Model.ThermalSpec import (
    ThermalSpec,
)
from convert.Formats.Fusion.DocumentCodec.Model.ConfigPart import ConfigPart
from convert.Formats.Fusion.DocumentCodec.Model.DocumentBody import DocumentBody
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSnap import DocumentSnap
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.DocumentCodec.Model.MaterialPart import MaterialPart
from convert.Formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec

# the document types order must stay explicit so public document claims remain grounded in native records
KDocumentTypes: tuple[type[object], ...] = (
    PrismSnapshot,
    RegionEdge,
    RegionFrame,
    MaterialSpec,
    MechanicSpec,
    DirectionValue,
    ThermalSpec,
    FinishSpec,
    ConfigPart,
    DocumentBody,
    DocumentModel,
    DocumentSnap,
    DocumentSpec,
    MaterialPart,
    ParsedSegment,
    FilletSpec,
    ChamferSpec,
    ShellSpec,
)
