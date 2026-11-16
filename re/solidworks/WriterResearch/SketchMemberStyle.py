from enum import IntEnum
from struct import Struct


# these are native standard-width values rather than custom widths in metres
class Weight(IntEnum):
    NONE = -1
    THIN = 0
    NORMAL = 1


VISUAL_PREFIX = Struct("<hHBIh")
STANDARD_WIDTH = Struct("<hf")
COLOR_STATUS_TYPE = Struct("<3H")
NO_LAYER = -1
ALL_BY_LAYER = 0x1F
INITIAL_VISUAL_STATE = 3
NO_COLOR = 0xFFFFFFFF
NO_STYLE = -1
NO_CUSTOM_WIDTH = -1.0


# the native enum constructor preserves the unset custom-width sentinel
def standard_width(weight: object) -> bytes:
    if not isinstance(weight, Weight):
        raise ValueError("expected a declared standard line weight")
    return STANDARD_WIDTH.pack(weight, NO_CUSTOM_WIDTH)


# ordinary profile members start with the constructor's inherited layer settings
def default_visual() -> bytes:
    return VISUAL_PREFIX.pack(
        NO_LAYER, ALL_BY_LAYER, INITIAL_VISUAL_STATE, NO_COLOR, NO_STYLE
    ) + standard_width(Weight.NONE)


# the structural member retains its unsolved constructor color and status
def initial_display_state() -> bytes:
    return COLOR_STATUS_TYPE.pack(5, 1, 1)
