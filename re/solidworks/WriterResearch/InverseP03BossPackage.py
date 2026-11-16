# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace
from datetime import timedelta
from math import isclose
from pathlib import PureWindowsPath
from struct import calcsize

from BossBridge import BindBossWriter
from BossOwners import BuildBossOwners, ConfigClocks, KMemberIds, SystemClocks
from CmgrBaseHeader import ReadCmgrHeader
from CmgrBossMass import CalcBossMass, ReadBossMass
from CmgrColorReadback import ReadColorSpan
from CmgrInherited import ArchiveFeature
from CmgrOpening import ReadCmgrFeature
from ContentManager import (
    CONTENT_MANAGER,
    ContentBody,
    ReadContentManager,
    UNSET_DENSITY,
)
from DefinitionTail import ReadPartDefinitionTail
from FreshBossConfig import FixtureCfgPrefs
from FreshPartMetadata import (
    AuthoredTimes,
    BuildFreshMetadata,
    MetadataContext,
    MetadataTimes,
)
from FusionP03BossLogical import InverseBoss
from HeaderLogs import ReadHeaderLogs
from HeaderSelf import ReadHeaderSelf
from HeaderTail import ReadHeaderTail
from OrdinaryConfig import BuildOrdinaryConfig
from OrdinaryPackage import (
    BuildOrdinaryPackage,
    KConfigManager,
    KDefinition,
    KModelHeader,
)
from PairedCaptureIntake import require, sha256
from PartFraming import CheckVersionStreams, KPartGeneration
from ResolvedPart import BuildOrdinaryResolved
from VerifyBossBridge import wire_state
from VerifyBossOpen import read_atom
from VerifyConfigMat import inspect_material
from VerifyFreshBoss import (
    FileClock,
    FixtureContext,
    FixturePackage,
    OWNER_IDS,
)
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KConfigStream,
    KResolvedFeaturesStream,
)
from convert.adapters.solidworks.Resolved.RectanglePart import ReadRectPart

# These independent native cache streams are not represented by the ordinary writer.
NATIVE_CACHE_MEMBERS = (
    "Contents/Config-0-Partition",
    "Contents/Config-0-GhostPartition",
    "Contents/Config-0-LWDATA",
    "Contents/DisplayLists",
)


# The explicit save context must agree with the source density on both Definition and Config paths.
def check_context(context: FixtureContext, density: float):
    identities = (
        context.BlockId,
        context.Exchange.RecordId,
        context.Objects.Folder,
        *context.Objects.Planes,
        context.Objects.Document,
        *context.Pmi.Keys,
    )
    require(
        context.Created.utcoffset() == timedelta(0)
        and context.Created.microsecond == 0
        and len(set(identities)) == len(identities)
        and all(identity.version == 4 for identity in identities)
        and PureWindowsPath(context.SavedPath).is_absolute()
        and PureWindowsPath(context.SavedPath).suffix.casefold() == ".sldprt"
        and context.Definition.TerminalValue == density,
        "Expected distinct authored context identities, a UTC save clock, and matching Definition density",
    )


# Allocate fresh target feature times without entering the fixed geometry fixture.
def bind_context(source: InverseBoss, context: FixtureContext):
    created = int(context.Created.timestamp())
    shared_time = FileClock(context.Created)
    title = PureWindowsPath(context.SavedPath).stem
    _, profile, boss = wire_state()
    profile = replace(
        profile,
        DatumTime=created,
        OriginTime=created,
        Feature=replace(
            profile.Feature, FileTime=FileClock(context.Created + timedelta(seconds=1))
        ),
        Trim=replace(
            profile.Trim,
            File=replace(profile.Trim.File, Title=title, SavedTime=created),
            ReferenceTime=created + 1,
        ),
    )
    boss = replace(
        boss,
        Feature=replace(
            boss.Feature, FileTime=FileClock(context.Created + timedelta(seconds=2))
        ),
        ReferenceTime=created + 2,
    )
    bound = BindBossWriter(source.logical, OWNER_IDS, profile, boss)
    prefs = FixtureCfgPrefs("metric")
    prefs = replace(
        prefs,
        Title=title,
        BlockIdentity=context.BlockId,
        DensityKgM3=source.density_kg_m3,
        Visual=replace(prefs.Visual, NativeAssetPath=context.AssetPath),
    )
    owners = BuildBossOwners(
        bound,
        prefs,
        ConfigClocks(
            GeometryStamp=151,
            DocumentUpdateStamp=167,
            BodyStamp=181,
            SketchBlock=shared_time,
            ExplodedView=shared_time,
        ),
        SystemClocks(
            Members={
                identity: ArchiveFeature(
                    101 + identity, KPartGeneration, 2026225, shared_time
                )
                for identity in KMemberIds
            },
            FrontTime=created,
            RightTime=created,
            OriginTime=created,
            OriginState=103,
        ),
    )
    view, *remaining_views = context.Definition.Views
    first, second = remaining_views
    definition = replace(
        context.Definition,
        Views=(
            replace(view, centre=tuple(value * 1e-3 for value in source.centroid_mm)),
            first,
            second,
        ),
    )
    metadata = BuildFreshMetadata(
        bound,
        owners.Config,
        owners.System,
        MetadataContext(
            UserName="Kit P03 inverse research",
            HistoryName=title,
            NextTreeId=35,
            Times=MetadataTimes(
                HistoryStart=created,
                Created=created,
                SummaryCreated=created,
                Modified=created + 4,
                Updated=created + 3,
                Profile=AuthoredTimes(Created=created + 1, Rebuilt=created + 2),
                Boss=AuthoredTimes(Created=created + 2, Rebuilt=created + 3),
            ),
            Header=context.Header,
            Definition=definition,
            ManagerTime=shared_time,
            PartTime=shared_time,
        ),
    )
    return bound, owners, metadata


# The resolved feature reader must independently return the actual native owners and anchored operands.
def read_geometry(archive, source, bound, generation):
    config = archive.require(KConfigStream)
    part = ReadRectPart(config, archive.require(KResolvedFeaturesStream), generation)
    atom = read_atom(config, generation)
    boss = part.Boss
    require(
        boss is not None
        and atom.Body == bound.Atom
        and part.Profile.FeatureId == OWNER_IDS.Profile
        and part.Reference.FeatureId == part.Origin.Support.FeatureId == 2
        and part.Datum.Geometry.NormalWorld == (0.0, 0.0, 1.0)
        and part.Profile.NameValue == source.logical.SketchName
        and boss["name"] == source.logical.FeatureName
        and boss["native_feature_id"] == OWNER_IDS.Operation
        and boss["profile_object"] == part.Profile.ObjectIndex
        and boss["transfer_object"] == atom.ObjectIndex,
        "The reopened candidate does not identify the same target sketch, datum, Origin, and Boss owners",
    )
    geometry = part.Profile.Geometry
    points = geometry["points_metres"][:4]
    require(
        all(
            isclose(value * 1000, expected, rel_tol=0, abs_tol=1e-9)
            for actual, corner in zip(
                points, source.logical.Profile.CornersMm, strict=True
            )
            for value, expected in zip(actual, corner, strict=True)
        ),
        "Candidate corners disagree with the directed source rectangle slots",
    )
    lines = {
        row["native_id"]: tuple(row["point_indices"])
        for row in geometry["lines"]
        if row["native_id"] >= 0
    }
    require(
        set(lines) == {edge.Identity for edge in source.logical.Profile.Edges}
        and all(
            set(lines[edge.Identity]) == set(edge.PointSlots)
            for edge in source.logical.Profile.Edges
        ),
        "Candidate outline does not resolve the four source-derived perimeter lines",
    )
    rows = geometry["length_dimensions"]
    expected_roles = (
        (source.logical.Width, OWNER_IDS.Width, [(0, 1), (3, 4)]),
        (source.logical.Height, OWNER_IDS.Height, [(0, 1), (2, 3)]),
    )
    transfers = {}
    for row, (expected, dimension, operands) in zip(rows, expected_roles, strict=True):
        require(
            (row["name"], row["native_id"], row["point_native_ids"])
            == (expected.Length.Name, dimension, operands)
            and isclose(
                row["metres"] * 1000,
                expected.Length.Millimetres,
                rel_tol=0,
                abs_tol=1e-9,
            ),
            "Reopened candidate sketch driver differs from its source-derived operand",
        )
        transfers[expected.Length.Name] = {
            "source_parameter": expected.Length.ParameterId,
            "owner_feature": part.Profile.FeatureId,
            "dimension_id": dimension,
            "point_operands": operands,
            "value_mm": row["metres"] * 1000,
        }
    end = boss["end_specification"]
    depth = boss["depth_display"]["dimension"]
    original = source.logical.Depth
    require(
        (
            end["direction"],
            end["conditions"],
            depth["parameter_name"],
            depth["native_dimension_id"],
        )
        == (0, (0, 0), original.Name, OWNER_IDS.Depth)
        and isclose(
            depth["metres"] * 1000, original.Millimetres, rel_tol=0, abs_tol=1e-9
        ),
        "Reopened candidate has the wrong positive blind depth owner or extent",
    )
    transfers[original.Name] = {
        "source_parameter": original.ParameterId,
        "owner_feature": boss["native_feature_id"],
        "dimension_id": depth["native_dimension_id"],
        "value_mm": depth["metres"] * 1000,
    }
    return {
        "datum_id": part.Reference.FeatureId,
        "dimensions": transfers,
        "line_point_indices": lines,
        "end": "positive one sided blind",
    }


# The saved mass is independently read from the actual CMgr and joined to two density sites.
def read_physical(archive, source, generation):
    density = source.density_kg_m3
    definition = archive.require(KDefinition)
    configured = inspect_material(
        archive.require(KConfigStream), generation, LoadPartLayouts(), density, False
    )[-1]
    _, _, cursor = ReadColorSpan(archive.require(KConfigManager), generation)
    ReadCmgrFeature(cursor, generation)
    ReadCmgrHeader(cursor, generation)
    saved = ReadBossMass(cursor, generation, 1)
    require(
        ReadPartDefinitionTail(
            definition, len(definition) - calcsize("<id"), generation
        )
        == configured
        == density
        and isclose(saved.VolumeM3 * 1e9, source.volume_mm3, rel_tol=0, abs_tol=1e-7)
        and isclose(
            saved.MassKg, source.volume_mm3 * density * 1e-9, rel_tol=0, abs_tol=1e-15
        )
        and all(
            isclose(actual * 1000, expected, rel_tol=0, abs_tol=1e-7)
            for actual, expected in zip(
                saved.CentroidM, source.centroid_mm, strict=True
            )
        ),
        "The candidate's saved density, analytic volume, centroid or mass differs",
    )
    return {
        "body_count": 1,
        "density_kg_m3": density,
        "volume_mm3": saved.VolumeM3 * 1e9,
        "centroid_mm": tuple(value * 1000 for value in saved.CentroidM),
        "mass_kg": saved.MassKg,
    }


# The saved model header has its own checked spatial bounds and allocated target identity.
def read_bounds(archive, source, generation):
    cursor, logs = ReadHeaderLogs(archive.require(KModelHeader), generation)
    ReadHeaderSelf(cursor, generation)
    bounds = ReadHeaderTail(cursor, generation).Bounds
    lengths = (
        source.logical.Width.Length.Millimetres,
        source.logical.Height.Length.Millimetres,
        source.logical.Depth.Millimetres,
    )
    require(
        logs.NextTreeId == 35
        and bounds.Minimum == (0.0, 0.0, 0.0)
        and all(
            isclose(saved * 1000, size, rel_tol=0, abs_tol=1e-9)
            for saved, size in zip(bounds.Maximum, lengths, strict=True)
        ),
        "Candidate header world bounds or native feature allocator disagree",
    )
    return (bounds.Minimum, bounds.Maximum)


# Read the independently authored compatibility labels without mistaking them for physical material.
def read_content(archive, context, owners, generation):
    content = ReadContentManager(generation, archive.require(CONTENT_MANAGER))
    atom = read_atom(archive.require(KConfigStream), generation)
    require(
        content.ConfigName == "Default"
        and (content.MaterialName, content.MaterialId)
        == (context.Content.MaterialName, context.Content.MaterialId)
        and content.Body
        == ContentBody(
            atom.AtomId, owners.Boss.Opening.Name, context.Content.BodyVisible
        )
        and content.Density == UNSET_DENSITY,
        "Saved target compatibility labels or body ownership differ from authored context",
    )
    return {
        "material_name": content.MaterialName,
        "material_id": content.MaterialId,
        "compatibility_density": content.Density,
        "body_label": content.Body.Name,
    }


# Construct and inspect the ordinary archive entirely in memory before releasing JSON evidence.
def verify_inverse_package(source: InverseBoss, context: FixtureContext):
    check_context(context, source.density_kg_m3)
    bound, owners, metadata = bind_context(source, context)
    generation = KPartGeneration
    config = BuildOrdinaryConfig(generation, owners.Config)
    resolved = BuildOrdinaryResolved(
        generation, config, owners.System, bound.Profile, bound.Boss
    )
    estimated = CalcBossMass(
        bound.Bounds.Minimum, bound.Bounds.Maximum, source.density_kg_m3
    )
    state = FixturePackage(context, owners, metadata, estimated)
    payload = BuildOrdinaryPackage(
        generation, owners.Config, config, resolved, bound.Profile, bound.Boss, state
    )
    archive = SldprtArchive.from_bytes(payload)
    require(
        archive.format_version == 4 and ContainerMo(archive.streams) == generation,
        "Wrong ordinary target container version",
    )
    CheckVersionStreams(generation, archive.streams)
    require(
        all(name not in archive.streams for name in NATIVE_CACHE_MEMBERS),
        "Unexpected native geometry cache in the ordinary target",
    )
    return {
        "in_memory_archive_sha256": sha256(payload),
        "member_count": len(archive.streams),
        "geometry": read_geometry(archive, source, bound, generation),
        "physical": read_physical(archive, source, generation),
        "bounds_metres": read_bounds(archive, source, generation),
        "authored_content_readback": read_content(archive, context, bound, generation),
        "absent_native_cache_members": NATIVE_CACHE_MEMBERS,
        "body_representation": "Analytic from the regenerated sketch and Boss with typed saved body and mass metadata",
        "native_body_rebuild": "unobserved",
    }
