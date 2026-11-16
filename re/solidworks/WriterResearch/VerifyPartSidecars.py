from hashlib import sha256
import json

from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require

from HeaderLogs import ReadHeaderLogs
from HeaderSelf import ReadHeaderSelf
from HeaderTail import ReadHeaderTail
from PartDocProperties import (
    CoreProperties,
    CustomSummary,
    EncodeDocumentProperties,
    ReadCoreProperties,
)
from PartFraming import KPartGeneration
from PartOle import EncodePartOle, ReadPartOle
from PartOpc import CORE_PROPERTIES, EncodePartOpc
from PartOpenTime import OPEN_TIME_STREAM, EncodePartOpenTime, ReadPartOpenTime
from PartProperties import CUSTOM_PROPERTIES, EncodePartProperties, ReadPartProperties
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


LICENSED_OMISSIONS = {
    "Contents/Config-0-Partition",
    "Contents/Config-0-LWDATA",
    "Contents/DisplayLists",
    "Contents/Config-0-GhostPartition",
}


def document_properties(generation, archive):
    cursor, logs = ReadHeaderLogs(archive.require("Header2"), generation)
    external = ReadHeaderSelf(cursor, generation)
    header = ReadHeaderTail(cursor, generation)
    core = CoreProperties(logs.UserName, header.CreationTime, external.ModifiedTime)
    require(
        ReadCoreProperties(generation, archive.require(CORE_PROPERTIES)) == core,
        "independent ModelHeader join to the native summary author and clocks",
    )
    members = EncodeDocumentProperties(generation, core, CustomSummary(False, 0))
    require(
        all(archive.require(name) == payload for name, payload in members.items()),
        "complete generated document property members",
    )
    return members


# compare each generated stream with its full extent and retain the native roster
def report():
    captures = {}
    package_captures = {}
    property_captures = {}
    rosters = set()
    generation = KPartGeneration
    fresh = CoreProperties("Writer & <Reader> \u0394", 1_700_000_000, 1_700_000_001)
    fresh_members = EncodeDocumentProperties(generation, fresh, CustomSummary(False, 0))
    require(
        ReadCoreProperties(generation, fresh_members[CORE_PROPERTIES]) == fresh,
        "caller timestamps and escaped UTF-8 author survive fresh serialization",
    )
    for recipe, asset, data, _, _ in principal_captures():
        if recipe != "P03":
            continue
        archive = SldprtArchive.from_bytes(data, asset["path"])
        streams = archive.streams
        require(ContainerMo(streams) == generation, "generation-19000 P03 sidecars")
        require(LICENSED_OMISSIONS <= streams.keys(), "source roster before omissions")
        rosters.add(tuple(sorted(streams.keys() - LICENSED_OMISSIONS)))
        inventory = ReadPartProperties(generation, archive.require(CUSTOM_PROPERTIES))
        embedded = ReadPartOle(generation, streams)
        encoded = EncodePartOle(generation, embedded)
        encoded[CUSTOM_PROPERTIES] = EncodePartProperties(generation, inventory)
        require(
            all(archive.require(name) == payload for name, payload in encoded.items()),
            "complete typed OLE and custom property sidecars",
        )
        captures[asset["sha256"]] = [(name, sha256(payload).hexdigest()) for name, payload in sorted(encoded.items())]
        properties = document_properties(generation, archive)
        property_captures[asset["sha256"]] = [
            (name, sha256(payload).hexdigest()) for name, payload in sorted(properties.items())
        ]
        package = EncodePartOpc(generation, properties)
        timing = ReadPartOpenTime(generation, archive.require(OPEN_TIME_STREAM))
        package[OPEN_TIME_STREAM] = EncodePartOpenTime(generation, timing)
        require(
            all(archive.require(name) == payload for name, payload in package.items()),
            "complete typed package manifests and timing metadata",
        )
        package_captures[asset["sha256"]] = [
            (name, sha256(payload).hexdigest()) for name, payload in sorted(package.items())
        ]
    require(len(rosters) == 1, "consistent retained P03 members")
    (roster,) = rosters
    require(len(roster) == 33, "licensed P03 retained member count")
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "replay_sha256": json_digest(captures),
        "package_sha256": json_digest(package_captures),
        "document_sha256": json_digest(property_captures),
        "retained_sha256": json_digest(roster),
    }


def json_digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
