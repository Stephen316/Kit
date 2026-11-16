"""Construct a SOLIDWORKS metadata container and compare pinned P01 bookkeeping."""

import argparse
import json
from pathlib import Path
from struct import Struct

from RectangleFields import (
    KApplicationBuild,
    KGeneration,
    REVISION,
    pinned_captures,
    read_rectangle_configuration,
    read_resolved_prelude,
    require,
    sha256,
)
from RectangularResolved import close_rectangle, read_rectangle_entry
from convert.adapters.solidworks.Config.ModelEntry import ReadModelEntry
from convert.adapters.solidworks.Config.RootFields import ModelAtomStart
from convert.adapters.solidworks.Config.RootLayout import KRootClass, LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import (
    ContainerMo,
    EncodeClass,
    KNullKind,
    ReadTag,
)
from convert.adapters.solidworks.Container.Bookkeeping import (
    EncodePartMeta,
    KConfigObjects as CONFIG_OBJECTS,
    KDisplayUpdate as DISPLAY_STAMP,
    KModelStamps as MODEL_STAMPS,
    PartStamps,
)
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from convert.adapters.solidworks.Container.Container import (
    BuildSldprt,
    Container,
    KDefaultFileId,
    SldprtArchive,
    Signature,
)
from convert.adapters.solidworks.Resolved.ResolvedHead import OpenResolved

CONFIGURATION = "Contents/Config-0"
RESOLVED = f"{CONFIGURATION}-ResolvedFeatures"
LOAD_CRITICAL = {
    "Contents/Definition",
    "Contents/CMgr",
    CONFIGURATION,
    f"{CONFIGURATION}-ModelHeader",
    "Header2",
    RESOLVED,
}
STAMP = Struct("<I")
MODEL_VALUES = Struct("<III")
RESOLVED_FIELDS = Struct("<iH")
PRE_ATOM_FIELDS = Struct("<IHi2i")


def metadata_streams(stamps):
    return EncodePartMeta(KGeneration, stamps)


def read_null(cursor):
    tag = ReadTag(cursor.BlobValue, cursor.Offset)
    require(tag.kind == KNullKind, "expected an absent metadata object")
    cursor.Offset += tag.size


def read_metadata(archive):
    objects = FieldCursor(archive.require(CONFIG_OBJECTS), 0)
    require(objects.ReadInts("<H") == (0,), "configuration objects are present")
    read_null(objects)
    choices = [objects.ReadText(), objects.ReadText()]
    require(
        choices == ["", ""] and objects.Offset == len(objects.BlobValue),
        "configuration references are outside the empty metadata scope",
    )
    stamps = PartStamps(*MODEL_VALUES.unpack(archive.require(MODEL_STAMPS)))
    display = FieldCursor(archive.require(DISPLAY_STAMP), 0)
    require(
        display.ReadInts("<I") == (stamps.update,),
        "display and model update stamps differ",
    )
    read_null(display)
    require(display.Offset == len(display.BlobValue), "unexpected display stream tail")
    return stamps


def metadata_container(stamps):
    streams = metadata_streams(stamps)
    raw = BuildSldprt(streams)
    archive = SldprtArchive.from_bytes(raw)
    require(
        archive.file_id == KDefaultFileId and archive.format_version == 4,
        "generated container does not use the admitted framing",
    )
    require(
        Container(raw) == Signature(KDefaultFileId),
        "generated directory signature differs",
    )
    require(
        archive.streams == streams and read_metadata(archive) == stamps,
        "generated metadata does not read back",
    )
    require(
        ContainerMo(archive.streams) is None
        and not LOAD_CRITICAL.intersection(archive.streams),
        "metadata container unexpectedly contains document-level sources",
    )
    return raw, {
        "scope": "solidworks-metadata-container",
        "sha256": sha256(raw),
        "bytes": len(raw),
        "container_version": archive.format_version,
        "file_id": archive.file_id,
        "stream_sizes": {name: len(data) for name, data in archive.streams.items()},
        "model_generation_marker": None,
        "absent_required_streams": sorted(LOAD_CRITICAL),
        "vendor_loadable": None,
        "application_usable": None,
    }


def config_split_fields(first_body_size, second_body_size):
    return STAMP.pack(first_body_size), STAMP.pack(second_body_size)


def resolved_header(map_next, root_entries):
    require(len(root_entries) < 0xFFFF, "resolved root list needs the wide count form")
    return RESOLVED_FIELDS.pack(map_next, len(root_entries))


def compare_dispatch(archive):
    config, resolved = archive.require(CONFIGURATION), archive.require(RESOLVED)
    model, _ = ReadModelEntry(config, LoadPartLayouts())
    _, atom_start, atom_count = ModelAtomStart(config, model)
    require(atom_count == 0, "expected the P01 sketch-only configuration")
    root_tag = EncodeClass(KRootClass, 1)
    require(
        config.startswith(root_tag) and ReadTag(config, 0).size == len(root_tag),
        "generated root dispatch differs",
    )
    first_start = len(root_tag)
    second_start = atom_start - PRE_ATOM_FIELDS.size
    first, second = config_split_fields(
        second_start - (first_start + STAMP.size),
        len(config) - (second_start + STAMP.size),
    )
    require(
        config[first_start : first_start + STAMP.size] == first
        and config[second_start : second_start + STAMP.size] == second,
        "generated split lengths differ",
    )
    config_map, _ = read_rectangle_configuration(config, KApplicationBuild)
    _, prefix = read_resolved_prelude(resolved, config_map, 18)
    cursor, rectangle = read_rectangle_entry(resolved, config_map, KApplicationBuild, 0)
    close_rectangle(cursor, rectangle, 0)
    # Cabinet children are nested, while the existing environment alias is a root entry.
    root_entries = (
        *prefix["folders"],
        prefix["environment_alias"],
        *prefix["principal_planes"],
        prefix["origin"],
        rectangle,
    )
    header = resolved_header(config_map.NextIndex, root_entries)
    require(resolved.startswith(header), "generated resolved root header differs")
    handoff = OpenResolved(header, config_map, len(root_entries))
    require(
        handoff.Offset == len(header)
        and handoff.NextIndex == config_map.NextIndex
        and handoff.Classes == config_map.Classes
        and handoff.Objects == config_map.Objects,
        "resolved dispatch did not inherit the completed configuration namespace",
    )
    return {
        "configuration_sha256": sha256(config),
        "resolved_sha256": sha256(resolved),
        "root_tag": [0, first_start],
        "split_offsets": [first_start, second_start],
        "segment_lengths": [STAMP.unpack(first)[0], STAMP.unpack(second)[0]],
        "resolved_next_index": handoff.NextIndex,
        "resolved_root_count": len(root_entries),
    }


def compare_report():
    measurements, captures = pinned_captures()
    cases = []
    for name, digest, source, reopen in captures:
        require(
            reopen["configuration"] == "Default" and reopen["body_count"] == 0,
            "historical native observation is outside the sketch-only default configuration",
        )
        archive = SldprtArchive.from_bytes(source, name)
        require(
            ContainerMo(archive.streams) == KGeneration,
            "unexpected document generation",
        )
        stamps = read_metadata(archive)
        require(
            all(
                archive.require(stream) == content
                for stream, content in metadata_streams(stamps).items()
            ),
            "generated archived bookkeeping differs",
        )
        cases.append(
            {
                "file": name,
                "source_sha256": digest,
                "stamps": stamps.__dict__,
                **compare_dispatch(archive),
            }
        )
    return {
        "scope": "p01-config-and-metadata-bookkeeping",
        "capture_revision": REVISION,
        "application_build": KApplicationBuild,
        "measurements": measurements,
        "cases": cases,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    operations = parser.add_subparsers(dest="operation", required=True)
    _ = operations.add_parser("compare", help="compare the six pinned P01 archives")
    emit = operations.add_parser(
        "emit", help="write a metadata-only research container"
    )
    emit.add_argument("destination", type=Path)
    emit.add_argument(
        "--created", required=True, type=int, help="positive Unix creation seconds"
    )
    emit.add_argument(
        "--update", required=True, type=int, help="document update counter"
    )
    emit.add_argument("--body", required=True, type=int, help="body change counter")
    args = parser.parse_args()
    if args.operation == "compare":
        report = compare_report()
    else:
        raw, report = metadata_container(
            PartStamps(args.created, args.update, args.body)
        )
        with args.destination.open("xb") as output:
            output.write(raw)
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
