from convert.Formats.Fusion.BodyInputs.CombineInputs import KCombineGuid, ReadCombInputs
from convert.Formats.Fusion.BodyInputs.MirrorInputs import KMirrorGuid, ReadMirrInputs
from convert.Formats.Fusion.BodyInputs.ScaleControls import KScaleGuid
from convert.Formats.Fusion.BodyInputs.ScaleInputs import ReadScaleInputs
from convert.Formats.Fusion.BodyInputs.ShellInputs import KShellGuid, ReadShellInputs
from interchange.Enums.EnumFeatures import FeatureKind

# typed native role readers expand independently without changing history dispatch
KBodyInputReaders = {
    KCombineGuid: ("Combine", FeatureKind.KBoolean, ReadCombInputs),
    KScaleGuid: ("Scale", FeatureKind.KScale, ReadScaleInputs),
    KShellGuid: ("Shell", FeatureKind.KShell, ReadShellInputs),
    KMirrorGuid: ("Mirror", FeatureKind.KMirror, ReadMirrInputs),
}
