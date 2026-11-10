# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.BodyInputs.BodyInput import BodyInputs
from convert.formats.Fusion.BodyInputs.InputRefs import (
    CheckPickPrefix,
    ReadInputPicks,
    ReadPickRefs,
)
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import KSelectProxy, SelectCursor
from convert.formats.Fusion.Topology.BodyAnchor import KAnchorGuid
from interchange.enums.EnumFeatures import BooleanOp

# the primary record stores tool and target lists on opposite sides of auxiliary anchors
KCombineGuid = "2A94257F-2020-4B19-9A68-103A2672F1B7"

# the input frame confirms that a feature owns the following operand lists
KCombineFrame = "2E3AC990-483D-4A55-8662-C064B976A957"

# native codes match the independently captured boolean operation
KCombineOps = (BooleanOp.KJoin, BooleanOp.KCutOperation, BooleanOp.KIntersect)


# only the documented root frame can qualify the adjacent operation fields
def CheckCombFrame(
    BulkData: bytes, Owners: dict[int, RecordSpan], FrameId: int, FeatureId: int
) -> None:
    Frame = SelectCursor(BulkData, Owners, FrameId, KCombineFrame)
    if (
        len(Frame.DataValue) != 58
        or Frame.TakeBytes(20) != bytes(20)
        or Frame.ReadWord() != 3
    ):
        raise ValueError("Unsupported Fusion Combine input frame")
    Frame.Offset = 40
    if ReadNativeRef(Frame) != FeatureId or Frame.TakeBytes(7) != bytes(7):
        raise ValueError("Fusion Combine input frame owner disagrees")


# separate native lists identify boolean roles even when a tool is consumed
def ReadCombInputs(
    BulkData: bytes, Owners: dict[int, RecordSpan], FeatureId: int
) -> BodyInputs:
    Cursor = SelectCursor(BulkData, Owners, FeatureId, KCombineGuid)
    CheckPickPrefix(Cursor)
    Operation = Cursor.ReadWord()
    if Operation >= len(KCombineOps) or Cursor.TakeBytes(4) != bytes(4):
        raise ValueError("Unsupported Fusion Combine operation")
    KeepFlag, ComponentFlag = Cursor.TakeBytes(2)
    if KeepFlag not in (0, 1) or ComponentFlag != 0:
        raise ValueError("Unsupported Fusion Combine component mode or keep flag")
    Frames = ReadPickRefs(Cursor, Owners, KCombineFrame)
    if len(Frames) != 1:
        raise ValueError("Fusion Combine does not have one input frame")
    CheckCombFrame(BulkData, Owners, Frames[0], FeatureId)
    Handle = Cursor.ReadLong()
    Tools = ReadPickRefs(Cursor, Owners, KSelectProxy)
    for _ in range(3):
        _ = ReadPickRefs(Cursor, Owners, KAnchorGuid)
    Targets = ReadPickRefs(Cursor, Owners, KSelectProxy)
    if not Tools or len(Targets) != 1 or Targets[0] in Tools:
        raise ValueError("Fusion Combine target and tool lists disagree")
    ToolPicks = tuple(
        PickValue
        for ProxyId in Tools
        for PickValue in ReadInputPicks(
            BulkData,
            Owners,
            FeatureId,
            ProxyId,
            "tool",
            5,
            {"DcFeatureOperationIdFlag": Handle},
        )
    )
    TargetPicks = ReadInputPicks(BulkData, Owners, FeatureId, Targets[0], "target", 4)
    if len(ToolPicks) != len(Tools) or len(TargetPicks) != 1:
        raise ValueError("Fusion Combine requires one body per role proxy")
    return BodyInputs(ToolPicks + TargetPicks, KCombineOps[Operation], bool(KeepFlag))
