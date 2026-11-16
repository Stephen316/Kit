# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isclose as IsClose
from pathlib import Path as FilePath

from PairedCaptureIntake import require as RequirePad

from PadReceipts import KPhases, ReadPadBytes

# the ordered perturbations independently vary the base or upper depth
KDepths = {
    "baseline-a": (10, 5),
    "baseline-b": (10, 5),
    "depth-3": (10, 3),
    "depth-8": (10, 8),
    "support-11": (11, 5),
}

# each saved archive has three separately labeled native observations
KSavedPhases = ("authored", "before_rebuild", "after_rebuild")


# numeric evidence must be finite and compare in the units recorded by the native capture
def CheckNear(Actual: float, Expected: float, Label: str) -> None:
    RequirePad(
        type(Actual) in (int, float)
        and type(Expected) in (int, float)
        and IsClose(Actual, Expected, abs_tol=1e-8, rel_tol=1e-11),
        f"Measured {Label} differs from its independent check",
    )


# coordinates require a value for every expected component
def CheckVector(Actual: list, Expected: list | tuple, Label: str) -> None:
    RequirePad(
        isinstance(Actual, list) and len(Actual) == len(Expected),
        f"Invalid {Label} vector",
    )
    for Value, Target in zip(Actual, Expected, strict=True):
        CheckNear(Value, Target, Label)


# four bracketing stock copies must retain the original bytes and one measured solid
def CheckControls(Directory: FilePath, Observations: dict, StockSha: str) -> None:
    First = Observations["authoring_control_before"]
    for PhaseName in KPhases:
        for Moment in ("before", "after"):
            Value = Observations[f"{PhaseName}_control_{Moment}"]
            FileName = f"{PhaseName}-{Moment}-stock.SLDPRT"
            RequirePad(
                Value["label"] == f"{Moment} {PhaseName}"
                and Value["private_stock_file"] == FileName
                and Value["native_sha256"] == StockSha
                and Value["closed_read_only"] is True
                and Value["open_status"] == {"errors": 0, "warnings": 0}
                and Value["body_count"] == 1
                and Value["volume_mm3"] > 0
                and Value["units_code"] == 5
                and Value["configuration"] == "Default",
                f"Unhealthy stock control: {FileName}",
            )
            ReadPadBytes(Directory, FileName, StockSha)
            CheckNear(Value["volume_mm3"], First["volume_mm3"], "stock volume")
            CheckVector(
                Value["center_of_mass_mm"], First["center_of_mass_mm"], "stock centroid"
            )
            RequirePad(
                len(Value["center_of_mass_mm"]) == 3,
                "Stock centroid must have three coordinates",
            )


# each operation must keep its positive blind driven dimension on the measured feature
def CheckNativePad(Feature: dict, TypeName: str, ParamName: str, Depth: float) -> None:
    (ParamValue,) = Feature["dimensions"]
    Measured = Feature["operation"]
    RequirePad(
        Feature["type"] == TypeName
        and Feature["suppressed"] is False
        and Feature["error_code"] == 0
        and Feature["warning"] is False
        and Measured["end_condition"] == 0
        and Measured["reverse_direction"] is False
        and Measured["both_directions"] is False
        and ParamValue["name"] == ParamName
        and ParamValue["driven_state"] == 2
        and ParamValue["full_name"].startswith(f"{ParamName}@{Feature['name']}@"),
        f"Unproved native blind dimension: {Feature['name']}",
    )
    CheckNear(Measured["depth_m"] * 1000, Depth, "native operation depth")
    CheckNear(ParamValue["system_value"] * 1000, Depth, "authored parameter depth")


# the base and upper regions corroborate the independent stacked prism geometry
def CheckSections(Measurement: dict, BaseDepth: float) -> None:
    Layout = (("RectangleSketch", 4, 800, 0), ("UpperSketch", 2, 100, BaseDepth))
    Sketches = Measurement["sketches"]
    RequirePad(len(Sketches) == 2, "Expected two native sketches")
    for Value, (NameValue, SupportType, AreaValue, Height) in zip(
        Sketches, Layout, strict=True
    ):
        RequirePad(
            Value["name"] == NameValue
            and Value["support_type"] == SupportType
            and len(Value["entities"]) == 4,
            f"Unexpected native sketch inventory: {NameValue}",
        )
        CheckNear(Value["section_area_mm2"], AreaValue, "native section area")
        CheckVector(
            Value["section_center_world_mm"], (20, 10, Height), "section centroid"
        )


# mass and centroid are recomputed from the independent rectangular design parameters
def CheckPadMeasure(Measurement: dict, Depths: tuple[int, int]) -> None:
    BaseDepth, TopDepth = Depths
    BaseVolume, TopVolume = 800 * BaseDepth, 100 * TopDepth
    Total = BaseVolume + TopVolume
    Centre = (
        BaseVolume * BaseDepth / 2 + TopVolume * (BaseDepth + TopDepth / 2)
    ) / Total
    RequirePad(
        Measurement["body_count"] == 1
        and Measurement["native_body"] == {"faces": 11, "edges": 24, "vertices": 16}
        and Measurement["equations"] == []
        and Measurement["units_code"] == 5
        and Measurement["configuration"] == "Default",
        "Native two-pad snapshot does not contain the expected one-solid topology",
    )
    CheckNear(Measurement["volume_mm3"], Total, "two-pad volume")
    CheckVector(Measurement["center_of_mass_mm"], (20, 10, Centre), "two-pad centroid")
    CheckSections(Measurement, BaseDepth)
    DesignNames = ("RectangleSketch", "BaseBoss", "UpperSketch", "UpperBoss")
    Features = [
        Value for Value in Measurement["feature_tree"] if Value["name"] in DesignNames
    ]
    RequirePad(
        tuple(Value["name"] for Value in Features) == DesignNames,
        "Native two-pad feature order changed",
    )
    CheckNativePad(Features[1], "Extrusion", "depth_mm", BaseDepth)
    CheckNativePad(Features[3], "ICE", "upper_depth_mm", TopDepth)
    Support = Measurement["upper_support"]
    RequirePad(
        Support["kind"] == 2
        and Support["parent_feature"] == "BaseBoss"
        and Support["resolve_state"] == 0
        and isinstance(Support["reference"], str)
        and bool(Support["reference"]),
        "Native upper sketch does not resolve to the base boss face",
    )
    CheckNear(Support["area_mm2"], 700, "support face area")
    CheckVector(Support["origin_world_mm"], (0, 0, BaseDepth), "support origin")
    CheckVector(Support["normal_world"], (0, 0, 1), "support normal")


# only the first reopened baseline carries the independent edit and restoration observations
def CheckEditGrid(CaseValue: dict) -> int:
    Variant = CaseValue["variant"]
    Depths = KDepths[Variant]
    RequirePad(
        (CaseValue["base_depth_mm"], CaseValue["upper_depth_mm"]) == Depths,
        f"Wrong native depths: {Variant}",
    )
    RequirePad(
        CaseValue["open"] == {"errors": 0, "warnings": 0},
        f"Native reopen was not clean: {Variant}",
    )
    for Stage in KSavedPhases:
        CheckPadMeasure(CaseValue[Stage], Depths)
    Edits = {"edit_upper": (10, 7), "edit_base": (11, 5), "restored": (10, 5)}
    Expected = set(Edits) if Variant == "baseline-a" else set()
    RequirePad(
        Expected == set(CaseValue).intersection(Edits),
        f"Unexpected native edit witnesses: {Variant}",
    )
    for Stage in Expected:
        CheckPadMeasure(CaseValue[Stage], Edits[Stage])
    return len(KSavedPhases) + len(Expected)
