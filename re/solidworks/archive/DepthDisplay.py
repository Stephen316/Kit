"""Keep the existing receipt shape while sharing the typed depth reader."""

from convert.adapters.solidworks.Resolved.BossDepth import ReadBossDepth


def display_report(display):
    dimension = {key: value for key, value in display["dimension"].items() if key != "value_offset"}
    return {**display, "dimension": dimension}


def read_depth_display(cursor, *args):
    return display_report(ReadBossDepth(cursor, *args))
