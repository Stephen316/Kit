# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Verify the complete native empty property-section XML against the pinned sources."""

from collections import Counter
from hashlib import sha256
import json
from xml.etree.ElementTree import fromstring as ParseXml

from PartSectionProperties import EncodeSectionProps, KConfigXml, KCustomXml
from PartSimpleProperties import KVTypes
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from convert.adapters.solidworks.Container.Container import SldprtArchive


# derive the document-level property value from its typed source node
def SummaryFlag(Data):
    Root = ParseXml(Data)
    Section = Root.find('propertySection[@name="DocumentSummaryInformation"]')
    require(Section is not None, "missing native summary property section")
    Prop = Section.find('property[@pid="22"]')
    require(Prop is not None, "missing native Boolean summary property")
    Value = Prop.findtext(f"{{{KVTypes}}}bool")
    require(Value in ("No", "Yes"), "unexpected native summary Boolean")
    return Value == "Yes"


# compare every complete payload and keep a canonical summary independent of personal metadata
def report():
    Cases = {}
    Counts = Counter()
    Shapes = {KConfigXml: set(), KCustomXml: set()}
    for Recipe, Asset, Raw, _, _ in principal_captures():
        Streams = SldprtArchive.from_bytes(Raw, Asset["path"]).streams
        Generated = EncodeSectionProps(SummaryFlag(Streams[KCustomXml]))
        Result = {}
        for Name, Payload in Generated.items():
            require(
                Payload == Streams[Name], f"typed {Name} differs on {Asset['sha256']}"
            )
            Digest = sha256(Payload).hexdigest()
            Shapes[Name].add(Digest)
            Result[Name] = Digest
        Counts[Recipe] += 1
        Cases[Asset["sha256"]] = Result
    require(
        Counts == {"P01": 6, "P03": 8}, "unexpected property section capture roster"
    )
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": Cases,
        "counts": dict(Counts),
        "distinct_payload_counts": {
            Name: len(Digests) for Name, Digests in Shapes.items()
        },
        "replay_sha256": sha256(
            json.dumps(Cases, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
