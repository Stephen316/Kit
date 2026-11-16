# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Compare complete generated information properties with pinned licensed archives."""

from collections import Counter
from hashlib import sha256
import json
from xml.etree.ElementTree import fromstring as ParseXml

from PartFraming import KPartGeneration
from PartInformation import EncodeInformation, KInfoXml, KInfoNs, KMassName
from PartSimpleProperties import KVTypes
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from convert.adapters.solidworks.Container.Container import SldprtArchive


# read the measured scalar values while the constructor owns every field position and alias
def TypedMetadata(Data):
    Root = ParseXml(Data)
    require(Root.tag == f"{{{KInfoNs}}}Properties", "native information root differs")
    (Section,) = list(Root)
    require(Section.tag == "propertySection", "native information section differs")
    Values = {}
    for Row in Section.findall("property"):
        Pid, Name = int(Row.attrib["pid"]), Row.attrib["name"]
        if Pid == 1:
            continue
        (Child,) = list(Row)
        require(Name not in Values, "duplicated native information property name")
        Typed = Child.tag
        if Typed == f"{{{KVTypes}}}i4":
            Values[Name] = int(Child.text)
        else:
            require(
                Typed == f"{{{KVTypes}}}lpstr",
                "unmodeled native information property variant",
            )
            Values[Name] = Child.text or ""
    return Values


# compare full encoded streams and record only stable source and output hashes
def report():
    Cases = {}
    Counts = Counter()
    TotalWithMass = 0
    for Recipe, Asset, Raw, _, _ in principal_captures():
        Source = SldprtArchive.from_bytes(Raw, Asset["path"]).require(KInfoXml)
        Values = TypedMetadata(Source)
        require(
            (KMassName in Values) == (Recipe == "P03"),
            "unexpected mass metadata layout",
        )
        Output = EncodeInformation(KPartGeneration, Values)
        require(
            Output == Source,
            f"complete typed information property stream differs: {Asset['sha256']}",
        )
        Counts[Recipe] += 1
        TotalWithMass += KMassName in Values
        Cases[Asset["sha256"]] = sha256(Output).hexdigest()
    require(Counts == {"P01": 6, "P03": 8}, "unexpected native information captures")
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": Cases,
        "counts": dict(Counts),
        "with_mass_summary": TotalWithMass,
        "replay_sha256": sha256(
            json.dumps(Cases, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
