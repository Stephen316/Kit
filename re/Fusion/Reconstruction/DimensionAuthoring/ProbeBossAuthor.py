# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace
from math import isfinite
from uuid import uuid4

import ProbeOrigin
from PairedCaptureIntake import require
from convert.Formats.Fusion.DocumentCodec.BuildBodyPart import BuildBodyPart
from convert.Formats.Fusion.DocumentCodec.CheckDocSpec import CheckDocSpec
from convert.Formats.Fusion.DocumentCodec.Defaults.BaseDefaults import BaseDefaults
from convert.Formats.Fusion.DocumentCodec.Defaults.ExtrudeDefaults import (
    ExtrudeDefaults,
)
from convert.Formats.Fusion.DocumentCodec.Defaults.MakeNumeric import MakeNumeric
from convert.Formats.Fusion.DocumentCodec.Defaults.SketchDefaults import SketchDefaults
from convert.Formats.Fusion.DocumentCodec.Extrusion.AddExtrudeMut import AddExtrudeMut
from convert.Formats.Fusion.DocumentCodec.Extrusion.LinkBodyMut import LinkBodyMut
from convert.Formats.Fusion.DocumentCodec.Extrusion.LinkExtrudeMut import LinkExtrudeMut
from convert.Formats.Fusion.DocumentCodec.Extrusion.LinkProfileMut import LinkProfileMut
from convert.Formats.Fusion.DocumentCodec.Foundation.AddCollectMut import AddCollectMut
from convert.Formats.Fusion.DocumentCodec.Foundation.AddComputeMut import AddComputeMut
from convert.Formats.Fusion.DocumentCodec.Foundation.AddGeometryMut import (
    AddGeometryMut,
)
from convert.Formats.Fusion.DocumentCodec.Foundation.AddRootsMut import AddRootsMut
from convert.Formats.Fusion.DocumentCodec.Foundation.AddUnitsMut import AddUnitsMut
from convert.Formats.Fusion.DocumentCodec.Foundation.LinkCompMut import LinkCompMut
from convert.Formats.Fusion.DocumentCodec.Foundation.LinkRootsMut import LinkRootsMut
from convert.Formats.Fusion.DocumentCodec.Materials.BuildMatPart import BuildMatPart
from convert.Formats.Fusion.DocumentCodec.Materials.LinkMaterialMut import (
    LinkMaterialMut,
)
from convert.Formats.Fusion.DocumentCodec.Model.CreateAuthor import CreateAuthor
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.DocumentCodec.PackDocument import PackDocument
from convert.Formats.Fusion.DocumentCodec.Rectangle.AddRectangle import AddRectangle
from convert.Formats.Fusion.DocumentCodec.Rectangle.LinkRectangle import LinkRectangle
from convert.Formats.Fusion.DocumentCodec.Rectangle.Dimensions.AddConstrMut import (
    AddConstrMut,
)
from convert.Formats.Fusion.DocumentCodec.Rectangle.Dimensions.AddDimMut import (
    AddDimMut,
)
from convert.Formats.Fusion.DocumentCodec.Rectangle.Dimensions.BindDimMut import (
    BindDimMut,
)
from convert.Formats.Fusion.DocumentCodec.Rectangle.Dimensions.LinkDimGraphMut import (
    LinkDimGraphMut,
)
from convert.Formats.Fusion.DocumentCodec.Rectangle.Dimensions.MakeDimAxes import (
    MakeDimAxes,
)
from convert.Formats.Fusion.DocumentCodec.Records.EmitDesign import EmitDesign
from convert.Formats.Fusion.DocumentCodec.Sketch.SketchRole import SketchRole
from convert.Formats.Fusion.DocumentCodec.Tapered.TaperParameter import TaperParameter
from convert.Formats.Fusion.DocumentCodec.Values.ReadObjects import ReadSeries

# The paired P03 saves distinguish the two sketch drivers from the Boss depth.
DRIVERS = ("width_mm", "height_mm", "depth_mm")

# Allocation follows native creation and runtime slots without duplicate global parameters.
PARAMETER_ROLES = ("width_model", "depth_model", "along_parameter", "taper_parameter")

# The paired positive baseline records place their size annotations 8 mm outside the perimeter.
SIZE_OFFSETS = ((0.0, -0.8, 0.0), (-0.8, 0.0, 0.0))


# The explicit blind distance and zero taper belong to the same extrusion feature.
def bind_boss_parameters(author):
    distance = author.SpecValue.LengthMm
    along = MakeNumeric("depth_mm", distance, "", author.Policy.ParamBirthday)
    along.update(
        creationIndex=3,
        dcParameter=author.Reference("along_binding"),
        expression=f"{distance:g} mm",
        isUserDefined=False,
        name="AlongDistance",
    )
    taper = TaperParameter(author)
    taper.update(creationIndex=4, userName="d4", expression="0.0 deg")
    for slot, role, parameter in ((3, "along", along), (4, "taper", taper)):
        model = role + "_parameter"
        binding = role + "_binding"
        update = binding + "_dynamic"
        owner = author.Reference("dc_extrude")
        author.Change(model, **parameter)
        author.Change(
            binding,
            value=parameter["value"],
            parameter=author.Reference(model),
            rparamId=slot,
            rrOwnerFeature=owner,
            rParentFeature=owner,
            rDynamicUpdateData=author.Reference(update),
        )
        author.Change(
            update,
            rOwnerNode=author.Reference(binding),
            timeStamp=author.Policy.TimeStamp,
        )


# Build the same corner coincidence as P01 and a complete four-parameter table.
def add_owned_sketch(author):
    bindings, dimensions = [], []
    ref = author.Reference
    axes = zip(MakeDimAxes(author.SpecValue), SIZE_OFFSETS, strict=True)
    for slot, (axis, offset) in enumerate(axes, start=1):
        axis = replace(axis, Offset=offset)
        AddDimMut(author, axis)
        BindDimMut(author, axis, slot, slot)
        role = axis.RoleName
        expression = f"{axis.LengthMm:g} mm"
        author.Change(
            role + "_model",
            userName=axis.ParamName,
            name=f"Linear Dimension-{slot + 1}",
            expression=expression,
        )
        set_literal_annotation(author, role + "_dimension", expression)
        bindings.append(ref(role + "_binding"))
        dimensions.append(ref(role + "_dimension"))
    author.Change(SketchRole(author), dimensions=dimensions)
    children = ReadSeries(author.FindEntity("dc_sketch").FieldValues["childNodes"])
    author.Change("dc_sketch", dcParameters=bindings, childNodes=[*children, *bindings])
    author.Change(
        "parameters", highWaterMark=4, children=[ref(role) for role in PARAMETER_ROLES]
    )
    author.Change("fragment", nextParamId=4)
    helper = author.FindEntity("parameter_names")
    helper.Subjects.extend(PARAMETER_ROLES)
    names = zip((*DRIVERS, "d4"), PARAMETER_ROLES, strict=True)
    author.Change(
        "parameter_names",
        parameterMap=[
            {"key": name, "value": ref(role)} for name, role in sorted(names)
        ],
    )
    LinkDimGraphMut(author)


# A directly owned driving parameter uses literal display text instead of a formula badge.
def set_literal_annotation(author, role, expression):
    groups = author.FindEntity(role).FieldValues["LinearDimensionInfo"]
    require(len(groups) == 2, "Unexpected generated linear annotation schema")
    info = groups[1]["fields"]
    require(
        info["bDriven"] is False and info["prefix"] == "fx: ",
        "Unexpected linear cache mode",
    )
    info.update(prefix="", text=expression)


# Explicit composition preserves the witnessed ownership order without replacing shared build functions.
def build_owned_design(spec):
    CheckDocSpec(spec)
    author = CreateAuthor(spec, str(uuid4()))
    author.Defaults.update(BaseDefaults())
    AddRootsMut(author)
    AddCollectMut(author, DirectOwned=True)
    for builder in (
        AddComputeMut,
        AddGeometryMut,
        AddUnitsMut,
        LinkCompMut,
        LinkRootsMut,
    ):
        builder(author)
    author.Defaults.update(SketchDefaults())
    AddRectangle(author)
    LinkRectangle(author)
    author.Defaults.update(ExtrudeDefaults())
    AddExtrudeMut(author)
    bind_boss_parameters(author)
    for builder in (LinkProfileMut, LinkExtrudeMut, LinkBodyMut, LinkMaterialMut):
        builder(author)
    AddConstrMut(author)
    ProbeOrigin.add_origin_coincidence(author)
    add_owned_sketch(author)
    return EmitDesign(author)


# The existing geometry material and container emitters consume the directly owned design unchanged.
def generate_boss(variant, sizes, body_name):
    require(
        len(sizes) == 3 and all(isfinite(value) and value > 0 for value in sizes),
        "Expected positive XY width, height and blind depth",
    )
    width, height, depth = sizes
    spec = DocumentSpec(
        Title=f"P03 {variant} source-derived Boss",
        ParamName=DRIVERS[2],
        LengthMm=depth,
        ProfileKind="cuboid",
        SketchName="RectangleSketch",
        ExtrusionName="BlindBoss",
        BodyName=body_name,
        WidthMm=width,
        DepthMm=height,
        ConstrainRectangle=True,
        WidthParamName=DRIVERS[0],
        DepthParamName=DRIVERS[1],
    )
    design = build_owned_design(spec)
    return PackDocument(
        design, spec.Title, BuildBodyPart(spec, design) + BuildMatPart(design)
    )
