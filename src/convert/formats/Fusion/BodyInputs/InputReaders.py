from convert.formats.Fusion.BodyInputs.CombineInputs import KCombineGuid, ReadCombInputs
from convert.formats.Fusion.BodyInputs.MirrorInputs import KMirrorGuid, ReadMirrInputs
from convert.formats.Fusion.BodyInputs.ScaleControls import KScaleGuid
from convert.formats.Fusion.BodyInputs.ScaleInputs import ReadScaleInputs
from convert.formats.Fusion.BodyInputs.ShellInputs import KShellGuid, ReadShellInputs
from interchange.enums.EnumFeatures import FeatureKind

# typed native role readers expand independently without changing history dispatch
KBodyInputReaders = {
    KCombineGuid: ("Combine", FeatureKind.KBoolean, ReadCombInputs),
    KScaleGuid: ("Scale", FeatureKind.KScale, ReadScaleInputs),
    KShellGuid: ("Shell", FeatureKind.KShell, ReadShellInputs),
    KMirrorGuid: ("Mirror", FeatureKind.KMirror, ReadMirrInputs),
}
