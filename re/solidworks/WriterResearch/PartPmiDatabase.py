# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Write ordinary sketched and Boss dimensions into the PMI database."""

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from uuid import UUID

from BossResolve import ResolvedBossState
from ExchangePack import OrderedMap, PackExchange
from OrdinaryProfile import OrdinaryProfile
from PackageIndices import DisplaySize, KMillimetres
from PartFeatureIndex import KConfiguration
from PartFraming import VersionStorage
from UnqlitePage import WriteSingleBucket
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

KPmiDb = "Contents/PMISemanticDataDB"
KFirstSketchVisual = 10


# each annotation record keeps its owned native object id and physical length
@dataclass(frozen=True, slots=True)
class PmiLength:
    Name: str
    Owner: str
    ObjectId: int
    Metres: float
    BossOwned: bool


# new annotation identities and the database clock belong to the current save
@dataclass(frozen=True, slots=True)
class PmiIndex:
    Keys: tuple[UUID, ...]
    Created: datetime


# short identities refer only to the dimension and full identities add one part component
def AnnotationId(Dimension: PmiLength, Component: str | None) -> str:
    Display = f"<objID={Dimension.ObjectId}>"
    if Component is None:
        return Display
    RequireArch(
        bool(Component) and not any(Char in Component for Char in "<>\0"),
        True,
        "ordinary PMI title for component reference",
    )
    return (
        Display
        + f"<config Name={KConfiguration},ID=0><component Name={Component}.SLDPRT>"
    )


# the plain dimension records one unrounded SI magnitude and its drafting precision
def DimensionValue(Dimension: PmiLength) -> OrderedMap:
    return OrderedMap(
        (
            ("class", "DimSemData"),
            ("dimItemName", ""),
            ("dimSubType", "Linear"),
            ("isBasic", False),
            ("isInspection", False),
            ("isReferenceOnly", False),
            ("valPrecision", 2),
            ("value", Dimension.Metres),
        )
    )


# the scoped first-save sketch has formatted text while the Boss only stores its value
def AnnotationRecord(Dimension: PmiLength, Component: str | None) -> OrderedMap:
    FullForm = Component is not None
    Display = ""
    if FullForm and not Dimension.BossOwned:
        Display = f" {DisplaySize(Dimension.Metres * 1000.0, KMillimetres):.2f} "
    Standard = (("dimBaseStd", 4),) if FullForm else ()
    return OrderedMap(
        (
            ("annoType", 1),
            ("bottomText", ""),
            ("cadText", f"{Dimension.Name}@{Dimension.Owner}"),
            *Standard,
            ("dimItems", (DimensionValue(Dimension),)),
            ("dimText", "<DIM>"),
            ("dimType", int(Dimension.BossOwned)),
            ("dimXpertAnnotation", False),
            ("dispListText", Display),
            ("iDString", AnnotationId(Dimension, Component)),
            ("instanceCount", 1),
            ("prefixText", ""),
            ("suffixText", ""),
            ("supressState", False),
            ("topText", ""),
        )
    )


# the ordinary PMI member covers two sketch-owned drivers and at most one Boss driver
def EncodePmiDb(
    Generation: int,
    Index: PmiIndex,
    Component: str | None,
    Dimensions: tuple[PmiLength, ...],
) -> bytes:
    VersionStorage(Generation)
    RequireArch(
        len(Dimensions) in (2, 3)
        and len(Index.Keys) == len(set(Index.Keys)) == len(Dimensions)
        and all(Key.version == 4 for Key in Index.Keys),
        True,
        "distinct ordinary PMI annotation keys",
    )
    Scope = (("width_mm", False), ("height_mm", False), ("depth_mm", True))
    RequireArch(
        tuple((Dimension.Name, Dimension.BossOwned) for Dimension in Dimensions),
        Scope[: len(Dimensions)],
        "ordinary PMI driver inventory",
    )
    RequireArch(
        all(
            Dimension.Owner
            and not any(Char in Dimension.Owner for Char in "@\0")
            and isfinite(Dimension.Metres)
            and Dimension.Metres > 0
            and (
                Dimension.ObjectId == 0
                if Dimension.BossOwned
                else Dimension.ObjectId > 0
            )
            for Dimension in Dimensions
        )
        and Dimensions[0].Owner == Dimensions[1].Owner
        and Dimensions[0].ObjectId != Dimensions[1].ObjectId,
        True,
        "owned PMI scalar identities and positive finite magnitudes",
    )
    Records = tuple(
        (str(Key).encode("ascii"), PackExchange(AnnotationRecord(Dimension, Component)))
        for Key, Dimension in zip(Index.Keys, Dimensions, strict=True)
    )
    return WriteSingleBucket(Index.Created, Records)


# the package uses the same sketch display and Boss owners as its generated features
def PmiDimensions(
    Profile: OrdinaryProfile, Boss: ResolvedBossState | None
) -> tuple[PmiLength, ...]:
    Dimensions = tuple(
        PmiLength(
            Length.Name,
            Profile.Feature.Name,
            KFirstSketchVisual + Slot,
            Length.Millimetres / 1000.0,
            False,
        )
        for Slot, Length in enumerate(Profile.Lengths)
    )
    if Boss is None:
        return Dimensions
    return (
        *Dimensions,
        PmiLength(
            Boss.Display.NameValue,
            Boss.Opening.Name,
            0,
            abs(Boss.Display.DepthMm) / 1000.0,
            True,
        ),
    )
