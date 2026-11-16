from hashlib import sha256
import json

from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require

from PartFraming import KPartGeneration
from PartOle import EncodePartOle, ReadPartOle
from PartProperties import CUSTOM_PROPERTIES, EncodePartProperties, ReadPartProperties
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


LICENSED_OMISSIONS = {
    "Contents/Config-0-Partition",
    "Contents/Config-0-LWDATA",
    "Contents/DisplayLists",
    "Contents/Config-0-GhostPartition",
}


# compare each generated stream with its full extent and retain the native roster
def report():
    captures = {}
    rosters = set()
    for recipe, asset, data, _, _ in principal_captures():
        if recipe != "P03":
            continue
        archive = SldprtArchive.from_bytes(data, asset["path"])
        streams = archive.streams
        generation = KPartGeneration
        require(ContainerMo(streams) == generation, "generation-19000 P03 sidecars")
        require(LICENSED_OMISSIONS <= streams.keys(), "source roster before omissions")
        rosters.add(tuple(sorted(streams.keys() - LICENSED_OMISSIONS)))
        properties = ReadPartProperties(generation, archive.require(CUSTOM_PROPERTIES))
        embedded = ReadPartOle(generation, streams)
        encoded = EncodePartOle(generation, embedded)
        encoded[CUSTOM_PROPERTIES] = EncodePartProperties(generation, properties)
        require(
            all(archive.require(name) == payload for name, payload in encoded.items()),
            "complete typed OLE and custom property sidecars",
        )
        captures[asset["sha256"]] = [(name, sha256(payload).hexdigest()) for name, payload in sorted(encoded.items())]
    require(len(rosters) == 1, "consistent retained P03 members")
    (roster,) = rosters
    require(len(roster) == 33, "licensed P03 retained member count")
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "replay_sha256": json_digest(captures),
        "retained_sha256": json_digest(roster),
    }


def json_digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
