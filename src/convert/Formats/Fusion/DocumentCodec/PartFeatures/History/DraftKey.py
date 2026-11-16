from typing import TypeAlias

from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity

# the draft key shape must stay shared so parametric feature reconstruction uses one contract for compatible values
KDraftKey: TypeAlias = tuple[object, ...]

# the draft node shape must stay shared so parametric feature reconstruction uses one contract for compatible values
KDraftNode: TypeAlias = tuple[KDraftKey, KJournalEntity]

# the draft state shape must stay shared so parametric feature reconstruction uses one contract for compatible values
KDraftState: TypeAlias = tuple[KDraftNode, ...]
