# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Replay both saved feature summaries from typed P01 and P03 facts."""

from argparse import ArgumentParser
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
from sys import stdin
from typing import cast, TypedDict
from xml.etree.ElementTree import Element, fromstring as ParseXml

from VerifyConfigRoot import CAPTURE_REVISION, principal_captures

from CmgrBossMass import CalcBossMass
from ConfigAtomManager import ConfigAtomBinding
from HeaderLogs import ReadHeaderLogs
from OrdinaryConfig import BuildOrdinaryConfig
from OrdinaryPackage import BuildOrdinaryPackage, KModelHeader
from PartFeatureIndex import EncodeFeatures, KFeatureNs, KFeaturesXml, PartIndex
from PartFraming import KPartGeneration
from PartKeywords import (
    EncodeKeywords,
    KDepth,
    KKeywordsXml,
    KKeywordPrefix,
    KeywordBoss,
    KeywordDrivers,
)
from ResolvedPart import BuildOrdinaryResolved
from SolidworksCensusInputs import require as RequireCapture
from VerifyBossOpen import read_atom
from VerifyFreshBoss import FixturePackage, FixtureState, NeedElement, ParseContext
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KConfigStream,
    KResolvedFeaturesStream,
)
from convert.adapters.solidworks.Resolved.RectanglePart import ReadRectPart


class FeatureAsset(TypedDict):
    path: str
    sha256: str


ReadInputs = cast(
    Callable[[], Iterable[tuple[str, FeatureAsset, bytes, object, object]]],
    principal_captures,
)
ReadAtom = cast(Callable[[bytes, int], ConfigAtomBinding], read_atom)
require = cast(Callable[[bool, str], None], RequireCapture)


# bind shared document metadata across the independent features and keywords xml roots
def ReadIdentity(Features: Element, Keywords: Element) -> PartIndex:
    Model = NeedElement(Features, f"{{{KFeatureNs}}}swModelList")[0]
    Saved = NeedElement(Features, f"{{{KFeatureNs}}}swHeader")[0]
    Configuration = NeedElement(Features, f"{{{KFeatureNs}}}swConfigurationList")[0]
    Created = Saved.attrib["swCreationTime"]
    Reference = Configuration.attrib["swReference"]
    require(
        Keywords.attrib == {"id": Created, "Name": Reference},
        "keyword document identity differs from the saved configuration",
    )
    return PartIndex(
        int(Created),
        Saved.attrib["swPath"],
        Model.attrib["swName"],
        int(Model.attrib["swLastModifiedStamp"]),
        Reference,
    )


# a missing display string cannot supply an authored length to the saved index
def ReadDisplay(Node: Element) -> tuple[str, Decimal]:
    if Node.text is None:
        raise ValueError("missing saved display length")
    return Node.attrib["Name"], Decimal(Node.text)


# saved driver values and owner IDs refer to the same non-system feature rows
def FeatureRows(Keywords: Element) -> tuple[Element, Element | None]:
    (Sketch,) = [
        Entry for Entry in Keywords.findall("Sketch") if Entry.get("Type") != "Origin"
    ]
    Extrusions = Keywords.findall("Extrusion")
    require(len(Extrusions) <= 1, "unexpected Boss index inventory")
    if not Extrusions:
        return Sketch, None
    (Boss,) = Extrusions
    return Sketch, Boss


# preserve the existing assembly verifier's display value interface
def ReadDrivers(
    Keywords: Element, Recipe: str
) -> tuple[str, KeywordDrivers, KeywordBoss | None]:
    Sketch, Extrusion = FeatureRows(Keywords)
    First, Second = Sketch.findall("Dimension")
    Drivers = ReadDisplay(First), ReadDisplay(Second)
    require(
        (Extrusion is not None) == (Recipe == "P03"), "unexpected Boss index inventory"
    )
    Boss = None
    if Extrusion is not None:
        (Depth,) = Extrusion.findall("Dimension")
        require(Depth.attrib == {"Name": KDepth}, "unexpected Boss display driver")
        Boss = (Extrusion.attrib["Name"], ReadDisplay(Depth)[1])
    return Sketch.attrib["Name"], Drivers, Boss


# the archive's configuration atom must independently corroborate its resolved boss ID
def ReadFeatureIds(Archive: SldprtArchive) -> tuple[int, int | None]:
    Config = Archive.require(KConfigStream)
    Resolved = Archive.require(KResolvedFeaturesStream)
    Part = ReadRectPart(Config, Resolved, KPartGeneration)
    if Part.Boss is None:
        require(Part.IsSketchOnly, "missing typed Boss in feature index input")
        return Part.Profile.FeatureId, None
    BossId = Part.Boss["native_feature_id"]
    require(
        ReadAtom(Config, KPartGeneration).Body.FeatureId == BossId,
        "Config and Resolved Boss IDs",
    )
    return Part.Profile.FeatureId, BossId


# sidecar row IDs can be checked without passing them into the writer
def ReadKeywordIds(Keywords: Element) -> tuple[int, int | None]:
    Sketch, Boss = FeatureRows(Keywords)
    return int(Sketch.attrib["id"]), None if Boss is None else int(Boss.attrib["id"])


# pass only typed display values and metadata into the constructors for all fourteen archives
def Report() -> dict[str, object]:
    Cases: dict[str, dict[str, str]] = {}
    Counts: Counter[str] = Counter()
    Orders: set[tuple[str, ...]] = set()
    Last = None
    for Recipe, Asset, Raw, _, _ in ReadInputs():
        Archive = SldprtArchive.from_bytes(Raw, Asset["path"])
        Features = Archive.require(KFeaturesXml)
        Keywords = Archive.require(KKeywordsXml)
        require(Keywords.startswith(KKeywordPrefix), "keyword index prefix differs")
        ParsedKeywords = ParseXml(Keywords[len(KKeywordPrefix) :])
        Part = ReadIdentity(ParseXml(Features), ParsedKeywords)
        Sketch, Drivers, Boss = ReadDrivers(ParsedKeywords, Recipe)
        SketchId, BossId = ReadFeatureIds(Archive)
        require(
            ReadKeywordIds(ParsedKeywords) == (SketchId, BossId), "saved keyword owners"
        )
        EncodedFeatures = EncodeFeatures(KPartGeneration, Part)
        EncodedKeywords = EncodeKeywords(
            Part, Sketch, Drivers, Boss, SketchTreeId=SketchId, BossTreeId=BossId
        )
        require(EncodedFeatures == Features, "complete feature index differs")
        require(EncodedKeywords == Keywords, "complete keyword index differs")
        Orders.add(tuple(Name for Name, _ in Drivers))
        Counts[Recipe] += 1
        Cases[Asset["sha256"]] = {
            KFeaturesXml: sha256(EncodedFeatures).hexdigest(),
            KKeywordsXml: sha256(EncodedKeywords).hexdigest(),
        }
        Last = Part, Sketch, Drivers, Boss, SketchId, BossId
    require(Counts == {"P01": 6, "P03": 8}, "unexpected feature index captures")
    if Last is None:
        raise ValueError("missing feature index control")
    Part, Sketch, Drivers, Boss, SketchId, BossId = Last
    Escaped = replace(Part, SavedPath="path & <part>.SLDPRT", DocumentReference="A&B")
    EscapedFeatures = ParseXml(EncodeFeatures(KPartGeneration, Escaped))
    EscapedKeywords = ParseXml(
        EncodeKeywords(
            Escaped, Sketch, Drivers, Boss, SketchTreeId=SketchId, BossTreeId=BossId
        )[len(KKeywordPrefix) :]
    )
    require(ReadIdentity(EscapedFeatures, EscapedKeywords) == Escaped, "XML escaping")
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": Cases,
        "counts": dict(Counts),
        "dimension_orders": len(Orders),
        "invalid_driver_refusals": VerifyDriverRefusals(
            Part, Sketch, Drivers, Boss, SketchId, BossId
        ),
        "invalid_owner_refusals": VerifyOwnerRefusals(
            Part, Sketch, Drivers, Boss, SketchId
        ),
        "replay_sha256": sha256(
            json.dumps(Cases, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


# reject duplicate or malformed display dimensions before the standalone member is emitted
def VerifyDriverRefusals(
    Part: PartIndex,
    Sketch: str,
    Drivers: KeywordDrivers,
    Boss: KeywordBoss | None,
    SketchId: int,
    BossId: int | None,
) -> int:
    Name = Drivers[0][0]
    Invalid = (
        (Drivers[0], Drivers[0]),
        ((Name, Decimal(0)), Drivers[1]),
        ((Name, Decimal("NaN")), Drivers[1]),
        (("unbound", Decimal(40)), Drivers[1]),
    )
    for BadDrivers in Invalid:
        try:
            EncodeKeywords(
                Part, Sketch, BadDrivers, Boss, SketchTreeId=SketchId, BossTreeId=BossId
            )
        except ValueError:
            continue
        raise AssertionError("invalid display dimension was written")
    return len(Invalid)


# the standalone XML writer refuses inconsistent or reserved tree owners on both lanes
def VerifyOwnerRefusals(
    Part: PartIndex,
    Sketch: str,
    Drivers: KeywordDrivers,
    Boss: KeywordBoss | None,
    SketchId: int,
) -> int:
    require(Boss is not None, "expected an authored Boss control")
    Invalid = (
        (Boss, 0, 67),
        (Boss, True, 67),
        (Boss, 0x80000000, 67),
        (Boss, 19, 67),
        (Boss, SketchId, 20),
        (Boss, SketchId, SketchId),
        (Boss, SketchId, None),
        (None, SketchId, 67),
    )
    for Feature, ProfileId, OperationId in Invalid:
        try:
            EncodeKeywords(
                Part,
                Sketch,
                Drivers,
                Feature,
                SketchTreeId=ProfileId,
                BossTreeId=OperationId,
            )
        except ValueError:
            continue
        raise AssertionError("invalid keyword owner was written")
    return len(Invalid)


# use the fresh fixture's independent typed state with new allocations before encoding
def VerifyFreshOwners(ContextText: str) -> dict[str, object]:
    Context = replace(ParseContext(ContextText), PreviewColors=None)
    Bound, Owners, Metadata = FixtureState(Context)
    Ids = (53, 67)
    Reassigned = dict(
        zip((Bound.Profile.Feature.TreeId, Bound.Atom.FeatureId), Ids, strict=True)
    )
    Profile = replace(
        Bound.Profile, Feature=replace(Bound.Profile.Feature, TreeId=Ids[0])
    )
    Configuration = replace(Owners.Config, Boss=replace(Bound.Atom, FeatureId=Ids[1]))
    CurrentLogs = Metadata.Header.Logs
    Logs = replace(
        CurrentLogs,
        Revisions=tuple(
            (
                replace(Log, TreeId=Reassigned[Log.TreeId])
                if Log.TreeId in Reassigned
                else Log
            )
            for Log in CurrentLogs.Revisions
        ),
        NextTreeId=max(Ids) + 1,
    )
    Metadata = replace(Metadata, Header=replace(Metadata.Header, Logs=Logs))
    OwnerStates = replace(Owners, Config=Configuration)
    Density = Configuration.First.DensityKgM3
    Mass = CalcBossMass(Bound.Bounds.Minimum, Bound.Bounds.Maximum, Density)
    State = FixturePackage(Context, OwnerStates, Metadata, Mass)
    Config = BuildOrdinaryConfig(KPartGeneration, Configuration)
    Resolved = BuildOrdinaryResolved(
        KPartGeneration, Config, Owners.System, Profile, Bound.Boss
    )
    Data = BuildOrdinaryPackage(
        KPartGeneration, Configuration, Config, Resolved, Profile, Bound.Boss, State
    )
    Archive = SldprtArchive.from_bytes(Data)
    Keywords = Archive.require(KKeywordsXml)
    require(Keywords.startswith(KKeywordPrefix), "generated keyword prefix")
    KeywordIds = ReadKeywordIds(ParseXml(Keywords[len(KKeywordPrefix) :]))
    TypedIds = ReadFeatureIds(Archive)
    _, Header = ReadHeaderLogs(Archive.require(KModelHeader), KPartGeneration)
    HeaderIds = tuple(Log.TreeId for Log in Header.Revisions[-2:])
    require(
        KeywordIds == TypedIds == HeaderIds == Ids, "generated feature index owners"
    )
    return {
        "keyword_feature_ids": KeywordIds,
        "typed_feature_ids": TypedIds,
        "header_feature_ids": HeaderIds,
        "member_count": len(Archive.streams),
    }


if __name__ == "__main__":
    Parser = ArgumentParser()
    Parser.add_argument(
        "--fresh-context",
        choices=("-",),
        help="verify fresh owner IDs using JSON on stdin",
    )
    Options = Parser.parse_args()
    Result = VerifyFreshOwners(stdin.read()) if Options.fresh_context else Report()
    print(json.dumps(Result, sort_keys=True))
