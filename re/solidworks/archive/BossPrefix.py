"""Expose the packaged extrusion parser to the saved report replay."""

from convert.adapters.solidworks.resolved.BossEnd import (
    ReadBossClose,
    ReadEndHead as read_end_prefix,
    ReadEndTail as read_end_tail,
)
from convert.adapters.solidworks.resolved.BossEntry import (
    ReadBodyReturn as read_body_feature_tail,
    ReadBossHead,
)

from DepthDisplay import display_report


def read_boss_close(cursor):
    boss = ReadBossClose(cursor)
    return {**boss, "depth_display": display_report(boss["depth_display"])}


def read_boss_prefix(cursor, boss, *, directions=(0,)):
    return ReadBossHead(cursor, boss, directions)
