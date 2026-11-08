# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping
from dataclasses import dataclass as MakeDataClass
from zipfile import ZipFile, ZipInfo

from convert.adapters.freecad.EditAxisRev.AxisReadCache import ReadAxisCache
from convert.adapters.freecad.EditBodyRev.BodyReadGraph import BodyGraph
from convert.adapters.freecad.EditBodyRev.BodyRevPlan import BodyRevPlan
from convert.adapters.freecad.EditBodyRev.PrismOrder import PrismOrder
from convert.adapters.freecad.EditExtRing import GetEditRing
from convert.adapters.freecad.EditRead.Sketch.SketchEvidence import (
    CheckCarriers,
    CheckEmptyFile,
)
from convert.adapters.freecad.EditRev.RevCacheProof import CheckRevWire
from convert.adapters.freecad.EditShape.PrismShape import IsEditPrism, KMaxPrismBytes
from convert.adapters.freecad.EditShape.Revolution.RevolveShape import (
    IsEditRevolve,
    KMaxRevolveBytes,
)
from convert.adapters.freecad.ReconcileEdit import ReadEditBrep
from convert.geometry.Extrude.Polygon.PrismRing import ReadPrismRing
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.Sketch import Sketch


# the two features and two sketches each own separate native evidence
@MakeDataClass(frozen=True, slots=True)
class BodyCaches:
    Seed: str
    Revolve: str
    Source: str
    Profile: str
    IsSeed: bool


# missing wire caches are expected only on a newly generated untouched seed graph
def ReadBodyCaches(Members: Mapping[str, ZipInfo], Graph: BodyGraph) -> BodyCaches:
    CheckCarriers(Graph.Objects, Members)
    Seed = ReadAxisCache(Graph.Seed, "Shape")
    Revolve = ReadAxisCache(Graph.Revolve, "Shape")
    Source = ReadAxisCache(Graph.Source, "Shape")
    Profile = ReadAxisCache(Graph.Profile, "Shape")
    for Native in (Graph.Source, Graph.Profile):
        CheckEmptyFile(Members, ReadAxisCache(Native, "InternalShape"))
    if not Seed or not Revolve or bool(Source) != bool(Profile):
        raise ValueError("FreeCAD editable body axis native caches are incomplete")
    IsSeed = not Source
    if any(
        Value.touched != IsSeed
        for Value in (Graph.Seed, Graph.Revolve, Graph.Source, Graph.Profile)
    ):
        raise ValueError("FreeCAD editable body axis rebuild is pending")
    return BodyCaches(Seed, Revolve, Source, Profile, IsSeed)


# each saved solid independently witnesses the rebuilt control graph and exact linked rim
def CheckBodyCaches(
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
    Caches: BodyCaches,
    OriginalSource: Sketch,
    OriginalProfile: Sketch,
    Document: CadDocument,
    Plan: BodyRevPlan,
    Order: PrismOrder,
) -> None:
    ById = {Value.id: Value for Value in Document.sketches}
    Source, Profile = ById[Plan.Extrude.SketchId], ById[Plan.Revolve.SketchId]
    CheckRevWire(
        Archive, Members, Caches.Source, (), OriginalSource, Source, Plan.SourceFrame
    )
    CheckRevWire(
        Archive,
        Members,
        Caches.Profile,
        (),
        OriginalProfile,
        Profile,
        Plan.ProfileFrame,
    )
    SeedData = ReadEditBrep(
        Archive, Members, Caches.Seed, KMaxPrismBytes, "editable body axis extrusion"
    )
    Lines = GetEditRing(Document.feature_timeline[1], Source)
    Start = Plan.AxisStart if Order.Base == Plan.AxisEnd else Plan.AxisEnd
    if Lines is None or not IsEditPrism(
        SeedData,
        Plan.SourceFrame,
        ReadPrismRing(Lines),
        Plan.Extrude.DistanceMm,
        Link=(int(Order.EdgeName.removeprefix("Edge")), Start, Order.Base),
    ):
        raise ValueError(
            "FreeCAD editable body axis extrusion cache disagrees with its linked rim"
        )
    RevData = ReadEditBrep(
        Archive, Members, Caches.Revolve, KMaxRevolveBytes, "editable body axis Revolve"
    )
    if not IsEditRevolve(RevData, Plan.RevolveModel):
        raise ValueError(
            "FreeCAD editable body axis Revolve cache disagrees with its live controls"
        )
