# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from io import BytesIO
from pathlib import Path as FilePath
from interchange import RevolutionFeature
from convert.adapters.solidworks.core.Adapter import (
    NativePartModel,
    ReadSldprt,
    WriteSldprt,
)
from convert.adapters.solidworks.container.Container import SldprtArchive

KSample = (
    FilePath(__file__).parents[4]
    / "examples"
    / "Single Turbo Dual Overhead Cam V8 - KDP - 2024"
    / "10MM x 20MM x 13MM head 316 Stainless Steel Socket Head Screw.SLDPRT"
)


def TestAxisOwner() -> None:
    Archive = SldprtArchive.open(KSample)
    Model = NativePartModel(Archive, None)
    Operation = next(
        ItemValue for ItemValue in Model.operations if ItemValue.object_id == 144
    )
    assert Operation.profile_id == 130
    assert Operation.axis_source_id == 63
    assert 63 in Operation.dependencies
    Document = ReadSldprt(KSample, include_brep=False)
    Feature = next(
        ItemValue
        for ItemValue in Document.feature_timeline
        if ItemValue.name == "Revolve1"
    )
    assert "sldprt:feature:63" in Feature.input_feature_ids
    assert Feature.sketch_id == "sldprt:sketch:130"
    Definition = Feature.definition
    assert isinstance(Definition, RevolutionFeature)
    if Operation.axis_marker_offset is None:
        assert Definition.axis_entity_id == "sldprt:sketch:63"
    else:
        AxisSketch = next(
            ItemValue
            for ItemValue in Document.sketches
            if ItemValue.id == "sldprt:sketch:63"
        )
        assert Definition.axis_entity_id in {
            ItemValue.id for ItemValue in AxisSketch.entities
        }
    Output = BytesIO()
    _ = WriteSldprt(Document, Output)
    Reopened = ReadSldprt(Output.getvalue(), include_brep=False)
    assert Reopened.feature_timeline == Document.feature_timeline
