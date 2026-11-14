from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import (
    PrismSnapshot,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionEdge import (
    RegionEdge,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionFrame import (
    RegionFrame,
)
from convert.formats.Fusion.DocumentCodec.Materials.Model.DirectionValue import (
    DirectionValue,
)
from convert.formats.Fusion.DocumentCodec.Materials.Model.FinishSpec import FinishSpec
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.formats.Fusion.DocumentCodec.Materials.Model.MechanicSpec import (
    MechanicSpec,
)
from convert.formats.Fusion.DocumentCodec.Materials.Model.ThermalSpec import (
    ThermalSpec,
)
from convert.formats.Fusion.DocumentCodec.Model.ConfigPart import ConfigPart
from convert.formats.Fusion.DocumentCodec.Model.DocumentBody import DocumentBody
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Model.DocumentSnap import DocumentSnap
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.Model.MaterialPart import MaterialPart
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec

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
