# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections.abc import Mapping
from zipfile import ZipFile, ZipInfo

from convert.adapters.freecad.EditShape.Revolution.RevolveShape import (
    IsEditRevolve,
    KMaxRevolveBytes,
)
from convert.adapters.freecad.EditShape.SavedSketchWire import (
    IsSketchCache,
    KMaxSketchBytes,
)
from convert.adapters.freecad.ReconcileEdit import ReadEditBrep
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import Transform


# the saved profile cache must independently confirm the editable line geometry
def CheckRevWire(
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
    SketchEntry: str,
    EmptyEntries: tuple[str, ...],
    Original: Sketch,
    Profile: Sketch,
    Frame: Transform,
) -> None:
    if any(
        NameValue not in Members or Members[NameValue].file_size
        for NameValue in EmptyEntries
    ):
        raise ValueError("FreeCAD editable Revolve has an additional or missing shape")
    if not SketchEntry:
        if Profile != Original:
            raise ValueError(
                "FreeCAD editable Revolve profile has no saved sketch shape"
            )
        return
    SketchData = ReadEditBrep(
        Archive, Members, SketchEntry, KMaxSketchBytes, "editable Revolve sketch"
    )
    if not IsSketchCache(
        SketchData, Profile, Frame, ClosedWire=True, AllowPcurves=True
    ):
        raise ValueError(
            "FreeCAD editable Revolve sketch cache disagrees with its profile"
        )


# verified face orientation and boundaries distinguish stale shapes of equal volume
def CheckRevSolid(
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
    ShapeEntry: str,
    Rebuilt: CadDocument,
) -> None:
    ShapeData = ReadEditBrep(
        Archive, Members, ShapeEntry, KMaxRevolveBytes, "editable Revolve"
    )
    if Rebuilt.brep is None or not IsEditRevolve(ShapeData, Rebuilt.brep):
        raise ValueError(
            "FreeCAD editable Revolve shape disagrees with its live controls"
        )
