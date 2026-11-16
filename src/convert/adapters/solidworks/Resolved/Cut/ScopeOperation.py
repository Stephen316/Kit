from struct import calcsize as CalcSize
from typing import Literal

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import (
    ArchiveCursor,
    FieldCursor,
)
from convert.adapters.solidworks.Resolved.BossEntry import OpNode, ReadBodyReturn
from convert.adapters.solidworks.Resolved.Cut.CutOpRead import ReadCutEnd
from convert.adapters.solidworks.Resolved.Cut.ScopeBodies import ReadScopeList
from convert.adapters.solidworks.Resolved.Cut.ScopeChoices import ReadChooserPair
from convert.adapters.solidworks.Resolved.Cut.ScopeChoiceProof import ScopeChoiceKeys
from convert.adapters.solidworks.Resolved.Cut.ScopePartition import ReadPartition
from convert.adapters.solidworks.Resolved.Cut.ScopeTransfers import (
    CheckScopeXfer,
    ReadScopeLead,
)
from convert.adapters.solidworks.Resolved.Cut.ScopeTypes import ScopeOwner, ScopedCut


# scope must close through the footer before the two observed body list routes can be exposed
def ReadScopedCut(
    Cursor: ArchiveCursor,
    CutValue: OpNode,
    Owners: tuple[ScopeOwner, ScopeOwner],
    CutEdges: frozenset[int],
) -> ScopedCut:
    RequireArch(
        {Owner.FileObject for Owner in Owners},
        {CutValue["file_ref_object"]},
        "scope owners and cut belong to this archive",
    )
    RequireArch(
        len({Owner.FeatureId for Owner in Owners})
        == len({Owner.BodyId for Owner in Owners})
        == 2,
        True,
        "two distinct earlier scope owners",
    )
    CutTransfers, ParentTransfers, AtomIds = ReadScopeLead(Cursor)
    Primary = ReadScopeList(Cursor, Owners, Primary=True)
    ScopeOffset = Cursor.Offset
    (ScopeWord,) = Cursor.ReadInts("<i")
    Choices = ReadChooserPair(Cursor, Owners, CutValue)
    First, Second = (
        ScopeChoiceKeys(Choice, Owner, CutValue, CutEdges)
        for Choice, Owner in zip(Choices, Owners, strict=True)
    )
    RequireArch(First, Second, "scope choosers retain the same cut side identities")
    ExtraChooser, Expanded = Cursor.ReadInts("<Hi")
    RequireArch(
        (ExtraChooser, Expanded), (0, 0), "witnessed empty expanded scope controls"
    )
    Later = ReadScopeList(Cursor, Owners, Primary=False)
    RequireArch(
        (ScopeWord, Primary["present"], Later["present"])
        in ((0, False, True), (1, True, False)),
        True,
        "witnessed all bodies or explicit scope shape",
    )
    KindValue: Literal["all_bodies", "explicit"] = (
        "explicit" if ScopeWord else "all_bodies"
    )
    Bodies = Primary["bodies"] if ScopeWord else Later["bodies"]
    Count = len(Bodies)
    RequireArch(
        tuple(BodyValue["recent_atom_id"] for BodyValue in Bodies),
        AtomIds[:Count],
        "scope body tails bind the reached atom ids",
    )
    CheckScopeXfer(Cursor, Owners, Count, CutTransfers, ParentTransfers)
    RequireArch(
        tuple(Choice["raw_centre_state"] for Choice in Choices),
        ((0, 0, 0), (0, 1, 0) if Count == 1 else (0, 0, 0)),
        "witnessed chooser states for the saved scope lists",
    )
    Partition = ReadPartition(Cursor, Bodies)
    ReadBodyReturn(Cursor)
    EndValue = ReadCutEnd(Cursor)
    RequireArch(
        (
            EndValue["conditions"],
            EndValue["depth_display"],
            EndValue["direction"],
            EndValue["flip"],
        ),
        ((1, 0), None, 0, 0),
        "witnessed depthless through all scope extent",
    )
    Footer = Cursor.Offset
    StartTail = FieldCursor(Cursor.BlobValue, Footer - CalcSize("<5idi"))
    RawStart = StartTail.ReadInts("<5i")
    RequireArch(Cursor.ReadInts("<i"), (0,), "resolved scope list footer")
    RequireArch(Cursor.Offset, len(Cursor.BlobValue), "complete resolved scope extent")
    return {
        **CutValue,
        "scope_kind": KindValue,
        "scope_body_ids": tuple(
            BodyValue["body_id"] for BodyValue in Primary["bodies"]
        ),
        "chooser_body_ids": (
            Choices[0]["earlier_body_id"],
            Choices[1]["earlier_body_id"],
        ),
        "scope_word": ScopeWord,
        "scope_word_offset": ScopeOffset,
        "expanded_scope_word": Expanded,
        "primary_bodies": Primary,
        "later_bodies": Later,
        "cut_transfers": CutTransfers,
        "parent_transfers": ParentTransfers,
        "atom_ids": AtomIds,
        "choosers": Choices,
        "partition": Partition,
        "end_specification": EndValue,
        "raw_start_words": RawStart,
        "footer_offset": Footer,
        "stream_end": Cursor.Offset,
        "next_map_index": Cursor.NextIndex,
    }
