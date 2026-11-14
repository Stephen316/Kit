from typing import TypeAlias

from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity

KDraftKey: TypeAlias = tuple[object, ...]
KDraftNode: TypeAlias = tuple[KDraftKey, KJournalEntity]
KDraftState: TypeAlias = tuple[KDraftNode, ...]
