# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Verify preview member integration on the independently authored Boss fixture."""

import json
import sys
from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from OrdinaryConfig import BuildOrdinaryConfig
from OrdinaryPackage import BuildOrdinaryPackage
from PartFraming import KPartGeneration
from PartPreview import DIB_SIZE, PNG_SIZE, BuildPreviewDrawing, RenderPartPreview
from PartPreviews import PREVIEW, PREVIEW_PNG
from ResolvedPart import BuildOrdinaryResolved
from VerifyConfigRoot import require
from VerifyFreshBoss import (
    CalcBossMass,
    FixturePackage,
    FixtureState,
    ParseContext,
    VerifyFreshBoss,
)
from VerifyPartPreviews import read_dib, read_png

from convert.adapters.solidworks.Container.Container import SldprtArchive

KPreviewColors = ((246, 247, 249), (20, 32, 40), (148, 171, 188))


# compare all preexisting members and independently decode both generated images
def VerifyPreviews(Context):
    Generation = KPartGeneration
    Baseline = replace(Context, PreviewColors=None)
    Bound, Owners, Metadata = FixtureState(Baseline)
    Config = BuildOrdinaryConfig(Generation, Owners.Config)
    Resolved = BuildOrdinaryResolved(
        Generation, Config, Owners.System, Bound.Profile, Bound.Boss
    )
    Density = Owners.Config.First.DensityKgM3
    Mass = CalcBossMass(Bound.Bounds.Minimum, Bound.Bounds.Maximum, Density)
    State = FixturePackage(Baseline, Owners, Metadata, Mass)
    Previous = BuildOrdinaryPackage(
        Generation, Owners.Config, Config, Resolved, Bound.Profile, Bound.Boss, State
    )
    require(
        VerifyFreshBoss(Baseline)["archive_sha256"] == sha256(Previous).hexdigest(),
        "independent preview choice preserves the existing fixture archive",
    )
    Updated = BuildOrdinaryPackage(
        Generation,
        Owners.Config,
        Config,
        Resolved,
        Bound.Profile,
        Bound.Boss,
        replace(State, PreviewColors=KPreviewColors),
    )
    Expected = SldprtArchive.from_bytes(Previous).streams
    Actual = SldprtArchive.from_bytes(Updated).streams
    require(
        set(Actual) - set(Expected) == {PREVIEW, PREVIEW_PNG}
        and all(Actual.get(Name) == Stream for Name, Stream in Expected.items()),
        "preview addition must preserve all generated feature and metadata members",
    )
    Profile = Bound.Profile
    Drawing = BuildPreviewDrawing(
        Profile.Attachment.DatumId,
        Profile.Corners,
        {Line.CreationId: Line.Endpoints for Line in Profile.Lines},
        min(Bound.Bounds.Minimum[2], 0.0) + max(Bound.Bounds.Maximum[2], 0.0),
    )
    Raster = RenderPartPreview(Generation, Drawing, KPreviewColors)
    DibWidth, DibHeight, DibPalette, DibIndices = read_dib(Actual[PREVIEW])
    require(
        (DibWidth, DibHeight, DibIndices) == (*DIB_SIZE, Raster.DibIndices)
        and DibPalette[:12]
        == bytes(
            Channel
            for Red, Green, Blue in KPreviewColors
            for Channel in (Blue, Green, Red, 0)
        ),
        "fresh DIB preserves color and exact top down geometry pixels",
    )
    require(
        read_png(Actual[PREVIEW_PNG]) == (*PNG_SIZE, (3779, 3779), Raster.PngRgba),
        "fresh PNG preserves its full RGBA raster and physical resolution",
    )
    return {
        "unchanged_members": len(Expected),
        "total_members": len(Actual),
        "source_archive_sha256": sha256(Previous).hexdigest(),
        "preview_archive_sha256": sha256(Updated).hexdigest(),
        "images": {
            PREVIEW: sha256(Actual[PREVIEW]).hexdigest(),
            PREVIEW_PNG: sha256(Actual[PREVIEW_PNG]).hexdigest(),
        },
    }


# use the same explicit context as the fixture without staging an external file
def Main() -> None:
    Parser = ArgumentParser(description="Verify preview members in a generated part")
    Parser.add_argument("--fixture-context", required=True)
    Input = Parser.parse_args().fixture_context
    Text = sys.stdin.read() if Input == "-" else Path(Input).read_text(encoding="utf-8")
    print(json.dumps(VerifyPreviews(ParseContext(Text)), sort_keys=True))


if __name__ == "__main__":
    Main()
