from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
import json
from struct import unpack_from
from xml.etree.ElementTree import fromstring

from CmgrIndex import KConfigurationIndex, ReadCmgrIndex
from DefinitionReadback import ReadModernPartDefinition
from HeaderLogs import ReadHeaderLogs
from HeaderSelf import ReadHeaderSelf
from HeaderTail import KFrameTolerance, ReadHeaderTail
from OrdinaryPackage import (
    BuildOrdinaryPackage,
    KConfigManager,
    KHeaderCopy,
    KModelHeader,
    PackageHeader,
    PackageManager,
    PackageState,
)
from PackageIndices import MakePartIndex, PackageXmlState
from PartDocProperties import CustomSummary, ReadCoreProperties
from PartFeatureIndex import KFeaturesXml
from PartInformation import KInfoXml
from PartKeywords import KKeywordsXml, KKeywordPrefix, KWidth
from PartFraming import CheckVersionStreams, VersionStorage
from PartOle import ReadPartOle
from PartOpc import CORE_PROPERTIES
from PartOpenTime import OPEN_TIME_STREAM, ReadPartOpenTime
from PartProperties import CUSTOM_PROPERTIES, ReadPartProperties
from VerifyBossOpen import verify_measured
from VerifyCmgrComposition import compare_cmgr_bytes, read_cmgr_document
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from VerifyModelHeader import FRAME_OFFSET, FRAME_WIDTH, measured_bounds
from VerifyPartFeatureIndex import ReadDrivers, ReadIdentity
from VerifyPartInformation import TypedMetadata
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Bookkeeping import KModelStamps
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KConfigStream,
    KResolvedFeaturesStream,
)
from convert.adapters.solidworks.Resolved.RectanglePart import ReadRectPart


# Independent file readers supply the semantic metadata and verify its shared owners.
def read_package(archive, generation, measurement):
    header = archive.require(KModelHeader)
    require(header == archive.require(KHeaderCopy), "native duplicate model header")
    cursor, logs = ReadHeaderLogs(header, generation)
    self_reference = ReadHeaderSelf(cursor, generation)
    frame = cursor.Offset + FRAME_OFFSET
    tail = ReadHeaderTail(cursor, generation)
    stamps = unpack_from("<3I", archive.require(KModelStamps))
    require(
        stamps == (tail.CreationTime, logs.UpdateStamp, tail.BodyStamp),
        "same part bookkeeping and model header owners",
    )
    core = ReadCoreProperties(generation, archive.require(CORE_PROPERTIES))
    require(
        (core.LastModifiedBy, core.ModifiedTime)
        == (logs.UserName, self_reference.ModifiedTime),
        "core summary and header share the modifier and saved clock",
    )
    manager, _, mass_at, mass = read_cmgr_document(archive, generation, measurement)
    index = ReadCmgrIndex(archive.require(KConfigurationIndex), generation)
    require(
        (index.NameValue, index.SessionStamp, index.LastSavedTime)
        == (manager.Opening.NameValue, logs.UpdateStamp, self_reference.ModifiedTime),
        "active index uses the same configuration and document counters",
    )
    feature_index = fromstring(archive.require(KFeaturesXml))
    saved_keywords = archive.require(KKeywordsXml)
    require(saved_keywords.startswith(KKeywordPrefix), "part keyword prefix")
    keywords = fromstring(saved_keywords[len(KKeywordPrefix) :])
    identity = ReadIdentity(feature_index, keywords)
    require(
        identity
        == MakePartIndex(
            identity.SavedPath,
            self_reference.File.Title,
            tail.CreationTime,
            logs.UpdateStamp,
        ),
        "feature index shares the file and model header identity",
    )
    _, drivers, _ = ReadDrivers(keywords, "P03" if measurement["body_count"] else "P01")
    state = PackageState(
        PackageHeader(
            logs, self_reference, replace(tail, Bounds=measured_bounds(measurement))
        ),
        PackageManager(
            manager.Opening, manager.Visual, manager.PartTime, manager.External.Flags
        ),
        ReadModernPartDefinition(archive.require("Contents/Definition"), generation),
        core.CreatedTime,
        CustomSummary(False, 0),
        ReadPartProperties(generation, archive.require(CUSTOM_PROPERTIES)),
        ReadPartOle(generation, archive.streams),
        ReadPartOpenTime(generation, archive.require(OPEN_TIME_STREAM)),
        PackageXmlState(
            identity.SavedPath,
            drivers[0][0] == KWidth,
            TypedMetadata(archive.require(KInfoXml)),
        ),
    )
    return state, frame, mass_at, mass


# The native header's model bounds are compared independently of its exact framing.
def compare_header(source, rendered, frame):
    end = frame + FRAME_WIDTH
    require(
        (source[:frame], source[end:]) == (rendered[:frame], rendered[end:]),
        "packaged model header outside its geometry frame",
    )
    require(
        all(
            abs(actual - expected) <= KFrameTolerance
            for actual, expected in zip(
                unpack_from("<10d", source, frame),
                unpack_from("<10d", rendered, frame),
                strict=True,
            )
        ),
        "packaged header geometry matches the independent native frame",
    )


def verify_feature_members(candidate, generation, config, resolved, measurement):
    streams = candidate.streams
    require(
        streams[KConfigStream] == config.Framed.Data
        and streams[KResolvedFeaturesStream] == resolved.Framed.Data,
        "no change to the generated configuration and resolved streams during assembly",
    )
    part = ReadRectPart(
        streams[KConfigStream], streams[KResolvedFeaturesStream], generation
    )
    require(
        int(part.Boss is not None) == measurement["body_count"],
        "packaged feature history agrees with the licensed body count",
    )
    if part.Boss is not None:
        verify_measured(part.Boss, measurement)


# Compose every currently typed member and independently unpack the result.
def verify_generated_package(
    archive, generation, measurement, configuration, config, resolved, profile, boss
):
    state, frame, mass_at, mass = read_package(archive, generation, measurement)
    data = BuildOrdinaryPackage(
        generation, configuration, config, resolved, profile, boss, state
    )
    candidate = SldprtArchive.from_bytes(data)
    streams = candidate.streams
    require(
        (candidate.format_version, ContainerMo(streams), len(streams))
        == (4, generation, 25),
        "ordinary generated package roster and version",
    )
    CheckVersionStreams(generation, streams)
    verify_feature_members(candidate, generation, config, resolved, measurement)
    header = streams[KModelHeader]
    require(header == streams[KHeaderCopy], "packaged model header duplicate")
    compare_header(archive.require(KModelHeader), header, frame)
    compare_cmgr_bytes(
        archive.require(KConfigManager),
        streams[KConfigManager],
        mass_at,
        mass,
        generation,
    )
    owned = {
        KConfigStream,
        KResolvedFeaturesStream,
        KModelHeader,
        KHeaderCopy,
        KConfigManager,
    }
    root = VersionStorage(generation) + "/"
    require(
        all(
            archive.require(name) == payload
            for name, payload in streams.items()
            if name not in owned and not name.startswith(root)
        ),
        "all other currently generated members match the pinned native contents",
    )


def report():
    captures = {}
    for _, asset, data, _, measurement in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        generation = ContainerMo(archive.streams)
        require(generation == 19000, "ordinary assembly generation")
        _, frame, mass_at, mass = read_package(archive, 19000, measurement)
        captures[asset["sha256"]] = [
            frame,
            mass_at,
            int(mass is not None),
            sha256(archive.require(KConfigManager)).hexdigest(),
        ]
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "replay_sha256": sha256(
            json.dumps(captures, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Inspect pinned metadata for whole part assembly"
    )
    _ = parser.parse_args()
    print(json.dumps(report(), sort_keys=True))
