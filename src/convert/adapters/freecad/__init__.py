# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.adapters.freecad.Adapter import (
    FreeCADAdapter as FreeCadAdapter,
    FreeCADAdapterError as FreeCadAdapterError,
    document_to_manifest as DocToManifest,
    extract_freecad_manifest as ExtractFreecadManifest,
    read_freecad as ReadFreecad,
    write_freecad as WriteFreecad,
)
from convert.adapters.freecad.Archive import (
    build_fcstd_archive as BuildFcstdArchive,
    extract_manifest_from_fcstd as ExtractManifestFromFcstd,
)

# this binding exists because shared behavior needs one stable value
KAllValue = [
    "FreeCADAdapter",
    "FreeCADAdapterError",
    "build_fcstd_archive",
    "document_to_manifest",
    "extract_freecad_manifest",
    "extract_manifest_from_fcstd",
    "read_freecad",
    "write_freecad",
]

# this binding exists because shared behavior needs one stable value
FreeCADAdapter = FreeCadAdapter

# this binding exists because shared behavior needs one stable value
FreeCADAdapterError = FreeCadAdapterError

# this binding exists because shared behavior needs one stable value
build_fcstd_archive = BuildFcstdArchive

# this binding exists because shared behavior needs one stable value
document_to_manifest = DocToManifest

# this binding exists because shared behavior needs one stable value
extract_freecad_manifest = ExtractFreecadManifest

# this binding exists because shared behavior needs one stable value
extract_manifest_from_fcstd = ExtractManifestFromFcstd

# this binding exists because shared behavior needs one stable value
read_freecad = ReadFreecad

# this binding exists because shared behavior needs one stable value
write_freecad = WriteFreecad
