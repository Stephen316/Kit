from ConfigResolvedFraming import (
    BeginConfigArchive,
    EncodeResolvedHeader,
    EncodeSplitLength,
    WriteConfigSplit,
    WriteResolvedEntry,
)
from ConfigRoot import WriteConfigRoot
from ConfigVisual import WriteConfigVisual
from PartArchive import PartArchiveState, PartArchiveWriter
from VerifyConfigVisual import read_visual
from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.RectanglePart import ReadRectPart
from convert.adapters.solidworks.Resolved.ResolvedHead import OpenResolved
from convert.adapters.solidworks.Resolved.SystemPrefix import ReadSysPrefix


def allocation_state(cursor: ArchiveCursor) -> PartArchiveState:
    return PartArchiveState(
        cursor.NextIndex,
        tuple(sorted(cursor.Classes.items())),
        tuple(sorted(cursor.Objects.items())),
    )


def verify_config_resolved(
    archive: SldprtArchive, generation: int
) -> dict[str, int | list[int]]:
    config = archive.require("Contents/Config-0")
    resolved = archive.require("Contents/Config-0-ResolvedFeatures")
    start, split, root, fields, visual_end, _, _ = read_visual(
        config, generation, LoadPartLayouts().Prefix
    )
    config_map, walk = ReadOrdinaryMap(config, generation)
    state = allocation_state(config_map)
    lengths = (split - start, len(config) - split - 4)
    RequireArch(
        (EncodeSplitLength(lengths[0]), EncodeSplitLength(lengths[1])),
        (config[start - 4 : start], config[split : split + 4]),
        "native Config-0 split lengths",
    )

    def write_owned_prefix(writer: PartArchiveWriter) -> None:
        WriteConfigRoot(writer, generation, root)
        WriteConfigVisual(
            writer, generation, fields, RealViewPresent=True, DspbrPresent=True
        )

    config_writer = BeginConfigArchive()
    WriteConfigSplit(config_writer, write_owned_prefix)
    prefix = config_writer.build()
    RequireArch(
        (prefix[: start - 4], prefix[start - 4 : start], prefix[start:]),
        (
            config[: start - 4],
            EncodeSplitLength(visual_end.Offset - start),
            config[start : visual_end.Offset],
        ),
        "composed typed Config-0 prefix and generated body length",
    )
    RequireArch(
        config_writer.Snapshot(),
        allocation_state(visual_end),
        "composed typed Config-0 prefix archive ownership",
    )

    part = ReadRectPart(config, resolved, generation)
    RequireArch(int(part.Boss is not None), walk["atom_count"], "resolved Boss root")
    loaded = OpenResolved(resolved, state.Cursor(config, len(config)), 18 + walk["atom_count"])
    system = ReadSysPrefix(loaded)
    roots = (
        *system.FirstFolders,
        system.Details,
        *system.LaterFolders,
        system.Environment,
        *system.Planes,
        part.Origin,
        part.Profile,
    )
    root_count = len(roots) + int(part.Boss is not None)
    RequireArch(
        EncodeResolvedHeader(state, root_count), resolved[:6], "resolved live-map header"
    )

    def write_environment(writer: PartArchiveWriter) -> None:
        writer.ReferenceObject(system.Environment, "moEnvFolder_c")

    resolved_writer = PartArchiveWriter(state)
    WriteResolvedEntry(resolved_writer, write_environment)
    RequireArch(
        resolved_writer.build(),
        resolved[system.EnvOffset : system.EnvOffset + 2],
        "resolved alias reuses the exact native Config-0 environment object",
    )
    return {
        "split_lengths": list(lengths),
        "config_next_slot": state.NextIndex,
        "resolved_root_count": root_count,
        "environment_slot": system.Environment,
    }
