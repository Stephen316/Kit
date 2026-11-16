from typing import TypeAlias

from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.BodyGridSpec import (
    BodyGridSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.BodyRingSpec import (
    BodyRingSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.CombineSpec import (
    CombineSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.SplitSpec import SplitSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.AxisSpec import AxisSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import (
    MirrorSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.MoveSpec import MoveSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.OffsetSpec import (
    OffsetSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PasteSpec import PasteSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.DraftSpec import DraftSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PointSpec import PointSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.RevolveSpec import (
    RevolveSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.LoftSpec import LoftSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.SweepSpec import (
    SweepSpec,
)

# the part feature variants need one shared contract so parametric feature reconstruction cannot omit a supported value shape
KPartFeature: TypeAlias = (  # lgtm[py/unused-global-variable]
    FilletSpec
    | ChamferSpec
    | ShellSpec
    | ExtrudeSpec
    | HoleSpec
    | PatternSpec
    | CircularSpec
    | MirrorSpec
    | PlaneSpec
    | AxisSpec
    | PointSpec
    | RevolveSpec
    | MoveSpec
    | OffsetSpec
    | DraftSpec
    | CombineSpec
    | SplitSpec
    | BodyGridSpec
    | BodyRingSpec
    | LoftSpec
    | SweepSpec
    | PasteSpec
)
