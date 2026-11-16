# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Replay both saved feature summaries from typed P01 and P03 facts."""

from collections import Counter
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
from xml.etree.ElementTree import fromstring as ParseXml

from PartFeatureIndex import EncodeFeatures, KFeatureNs, KFeaturesXml, PartIndex
from PartFraming import KPartGeneration
from PartKeywords import EncodeKeywords, KDepth, KKeywordsXml, KKeywordPrefix
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from convert.adapters.solidworks.Container.Container import SldprtArchive


# bind shared document metadata across the independent features and keywords xml roots
def ReadIdentity(Features, Keywords):
    Model = Features.find(f"{{{KFeatureNs}}}swModelList")[0]
    Saved = Features.find(f"{{{KFeatureNs}}}swHeader")[0]
    Configuration = Features.find(f"{{{KFeatureNs}}}swConfigurationList")[0]
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


# compare the sketch and Boss ownership from independently parsed display fields
def ReadDrivers(Keywords, Recipe):
    (Sketch,) = [
        Entry for Entry in Keywords.findall("Sketch") if Entry.get("Type") != "Origin"
    ]
    Drivers = tuple(
        (Node.attrib["Name"], Decimal(Node.text))
        for Node in Sketch.findall("Dimension")
    )
    Extrusions = Keywords.findall("Extrusion")
    require(len(Extrusions) == (Recipe == "P03"), "unexpected Boss index inventory")
    Boss = None
    if Extrusions:
        (Extrusion,) = Extrusions
        (Depth,) = Extrusion.findall("Dimension")
        require(Depth.attrib == {"Name": KDepth}, "unexpected Boss display driver")
        Boss = (Extrusion.attrib["Name"], Decimal(Depth.text))
    return Sketch.attrib["Name"], Drivers, Boss


# pass only typed display values and metadata into the constructors for all fourteen archives
def Report():
    Cases = {}
    Counts = Counter()
    Orders = set()
    for Recipe, Asset, Raw, _, _ in principal_captures():
        Archive = SldprtArchive.from_bytes(Raw, Asset["path"])
        Features = Archive.require(KFeaturesXml)
        Keywords = Archive.require(KKeywordsXml)
        require(Keywords.startswith(KKeywordPrefix), "keyword index prefix differs")
        ParsedKeywords = ParseXml(Keywords[len(KKeywordPrefix) :])
        Part = ReadIdentity(ParseXml(Features), ParsedKeywords)
        Sketch, Drivers, Boss = ReadDrivers(ParsedKeywords, Recipe)
        EncodedFeatures = EncodeFeatures(KPartGeneration, Part)
        EncodedKeywords = EncodeKeywords(Part, Sketch, Drivers, Boss)
        require(EncodedFeatures == Features, "complete feature index differs")
        require(EncodedKeywords == Keywords, "complete keyword index differs")
        Orders.add(tuple(Name for Name, _ in Drivers))
        Counts[Recipe] += 1
        Cases[Asset["sha256"]] = {
            KFeaturesXml: sha256(EncodedFeatures).hexdigest(),
            KKeywordsXml: sha256(EncodedKeywords).hexdigest(),
        }
    require(Counts == {"P01": 6, "P03": 8}, "unexpected feature index captures")
    Escaped = replace(Part, SavedPath="path & <part>.SLDPRT", DocumentReference="A&B")
    EscapedFeatures = ParseXml(EncodeFeatures(KPartGeneration, Escaped))
    EscapedKeywords = ParseXml(
        EncodeKeywords(Escaped, Sketch, Drivers, Boss)[len(KKeywordPrefix) :]
    )
    require(ReadIdentity(EscapedFeatures, EscapedKeywords) == Escaped, "XML escaping")
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": Cases,
        "counts": dict(Counts),
        "dimension_orders": len(Orders),
        "invalid_driver_refusals": VerifyDriverRefusals(Part, Sketch, Drivers, Boss),
        "replay_sha256": sha256(
            json.dumps(Cases, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


# reject duplicate or malformed display dimensions before the standalone member is emitted
def VerifyDriverRefusals(Part, Sketch, Drivers, Boss):
    Name = Drivers[0][0]
    Invalid = (
        (Drivers[0], Drivers[0]),
        ((Name, Decimal(0)), Drivers[1]),
        ((Name, Decimal("NaN")), Drivers[1]),
        (("unbound", Decimal(40)), Drivers[1]),
    )
    for BadDrivers in Invalid:
        try:
            EncodeKeywords(Part, Sketch, BadDrivers, Boss)
        except ValueError:
            continue
        raise AssertionError("invalid display dimension was written")
    return len(Invalid)


if __name__ == "__main__":
    print(json.dumps(Report(), sort_keys=True))
