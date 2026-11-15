"""Expose packaged chooser parsing to the saved report replay."""

from convert.adapters.solidworks.resolved.BossChooser import (
    CheckChoiceOwn as require_chooser_owner,
    ReadBossChoices as read_boss_choosers,
    ReadChoiceTail,
)


def read_chooser_tail(cursor, pointer_kind, body_ids=(0,)):
    return ReadChoiceTail(cursor, pointer_kind, body_ids)
