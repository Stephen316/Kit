# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass

from convert.adapters.freecad.EditRead.EditObjects import RequireEditObj
from convert.adapters.freecad.EditRead.Revolve.RevGraph import RequireRevName
from convert.adapters.freecad.EditRead.Revolve.RevGraphLinks import RequireRevProp
from convert.adapters.freecad.Native import NativeObject
from interchange.document.models.DocumentModel import CadDocument


# resolved native identities retain separate source group and feature ordering
@MakeDataClass(frozen=True, slots=True)
class PlaneNodes:
    Sheet: NativeObject
    Profile: NativeObject
    BodyValue: NativeObject
    Config: NativeObject
    Timeline: tuple[NativeObject, ...]
    Planes: dict[str, NativeObject]
    Picks: dict[str, NativeObject]


# each neutral entity must name exactly one native object of the declared type
def ReadPlaneNodes(
    Objects: tuple[NativeObject, ...], DocValue: CadDocument
) -> PlaneNodes:
    return PlaneNodes(
        RequireRevName(
            {Value.name: Value for Value in Objects}, "Parameters", "Spreadsheet::Sheet"
        ),
        RequireEditObj(Objects, DocValue.sketches[0].id, "Sketcher::SketchObject"),
        RequireEditObj(Objects, DocValue.bodies[0].id, "App::DocumentObjectGroup"),
        RequireRevProp(
            Objects,
            "KitConfigurationId",
            DocValue.configurations[0].id,
            "App::FeaturePython",
        ),
        tuple(
            RequireEditObj(
                Objects,
                StepValue.id,
                (
                    "Part::Revolution"
                    if Index == len(DocValue.feature_timeline) - 1
                    else "Part::Feature"
                ),
            )
            for Index, StepValue in enumerate(DocValue.feature_timeline)
        ),
        {
            PlaneValue.id: RequireEditObj(Objects, PlaneValue.id, "App::Plane")
            for PlaneValue in DocValue.support_planes
        },
        {
            PickValue.id: RequireRevProp(
                Objects, "KitSelectionId", PickValue.id, "App::FeaturePython"
            )
            for PickValue in DocValue.selections
        },
    )
