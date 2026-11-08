# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.BodyInputs.CombineInputs import KCombineGuid, ReadCombInputs
from convert.formats.Fusion.BodyInputs.MirrorInputs import KMirrorGuid, ReadMirrInputs
from convert.formats.Fusion.BodyInputs.ScaleInputs import KScaleGuid, ReadScaleInputs
from convert.formats.Fusion.BodyInputs.ShellInputs import KShellGuid, ReadShellInputs
from interchange.enums.EnumFeatures import FeatureKind

# typed native role readers expand independently without changing history dispatch
KBodyInputReaders = {
    KCombineGuid: ("Combine", FeatureKind.KBoolean, ReadCombInputs),
    KScaleGuid: ("Scale", FeatureKind.KScale, ReadScaleInputs),
    KShellGuid: ("Shell", FeatureKind.KShell, ReadShellInputs),
    KMirrorGuid: ("Mirror", FeatureKind.KMirror, ReadMirrInputs),
}
