# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Verify all ordinary application, core and open-time property records."""

from collections import Counter
from datetime import datetime as DateTime
from hashlib import sha256
import json
from xml.etree.ElementTree import fromstring as ParseXml

from PartSimpleProperties import (
    KAppProps,
    KCoreProps,
    KOpenProps,
    AppProperties,
    CoreProperties,
    OpenProperties,
    EncodeAppProps,
    EncodeCoreProps,
    EncodeOpenProps,
)
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from convert.adapters.solidworks.Container.Container import SldprtArchive


# pinned receipt XML exposes values rather than supplying any bytes to the writer
def XmlValues(Data):
    Root = ParseXml(Data)
    return {Child.tag.rsplit("}", 1)[-1]: Child.text or "" for Child in Root}


# each individual native property document keeps its own typed value state
def Application(Values):
    Flags = tuple(
        Values[Field] for Field in ("LinksUpToDate", "SharedDoc", "HyperlinksChanged")
    )
    require(set(Flags) <= {"true", "false"}, "app flag dialect")
    UpToDate, Shared, Hyper = (Value == "true" for Value in Flags)
    return AppProperties(
        Values["Template"],
        int(Values["TotalTime"]),
        Values["Application"],
        int(Values["DocSecurity"]),
        Values["Company"],
        UpToDate,
        Shared,
        Hyper,
        Values["AppVersion"],
    )


# reread lexical times as UTC values independently of XML byte representation
def Timestamped(Values):
    return CoreProperties(
        Values["lastModifiedBy"],
        DateTime.fromisoformat(Values["created"]),
        DateTime.fromisoformat(Values["modified"]),
    )


# the individual open-time display field appears in only one of the three witnessed states
def Opening(Values):
    return OpenProperties(
        int(Values["count"]),
        int(Values["TotalFileOpenTime"]),
        int(Values["LWcount"]),
        int(Values["LWTotalFileOpenTime"]),
        Values.get("FileOpenTime"),
    )


# count and pin complete emitted fields while withholding per-file metadata from the report
def report():
    Named = (
        (KAppProps, Application, EncodeAppProps),
        (KCoreProps, Timestamped, EncodeCoreProps),
        (KOpenProps, Opening, EncodeOpenProps),
    )
    Cases = {}
    Distinct = {Name: set() for Name, _, _ in Named}
    Counts = Counter()
    for Recipe, Asset, Raw, _, _ in principal_captures():
        Streams = SldprtArchive.from_bytes(Raw, Asset["path"]).streams
        Result = {}
        for Name, Assemble, Encode in Named:
            Source = Streams[Name]
            Encoded = Encode(Assemble(XmlValues(Source)))
            require(Encoded == Source, f"typed {Name} differs on {Asset['sha256']}")
            Digest = sha256(Encoded).hexdigest()
            Distinct[Name].add(Digest)
            Result[Name] = Digest
        Counts[Recipe] += 1
        Cases[Asset["sha256"]] = Result
    require(Counts == {"P01": 6, "P03": 8}, "unexpected simple property capture roster")
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": Cases,
        "counts": dict(Counts),
        "distinct_payload_counts": {
            Name: len(Digests) for Name, Digests in Distinct.items()
        },
        "replay_sha256": sha256(
            json.dumps(Cases, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
