from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

# the feature constructor retains the base precision flags and sets these route and generation flags
KMaskTwoDefaults = 0xFC | sum(1 << Bit for Bit in (0, 14, 17, 21, 22, 23, 29, 30, 31))

# the feature constructor sets these flags before the dimension settings replace bit twelve
KMaskThreeDefaults = (
    0x1870 | sum(1 << Bit for Bit in (0, 2, 9, 14, 16, 17, 18, 19))
) & ~(1 << 12)


# the source model supplies the preferences that the native constructor reads
@DataClass(frozen=True, slots=True, kw_only=True)
class DisplayPrefs:
    design_intent: bool
    inward_tolerance_rounding: bool
    remove_zero: bool
    uppercase_dimension: bool


# each named setting controls one bit independently of the solved geometry
def ComposeMasks(Preferences: DisplayPrefs) -> tuple[int, int]:
    Fields = (
        Preferences.design_intent,
        Preferences.inward_tolerance_rounding,
        Preferences.remove_zero,
        Preferences.uppercase_dimension,
    )
    RequireArch(
        all(type(Value) is bool for Value in Fields),
        True,
        "explicit distance display preferences",
    )
    DesignIntent, RoundInward, RemoveZero, Uppercase = Fields
    return (
        KMaskTwoDefaults | (DesignIntent << 8),
        KMaskThreeDefaults
        | (RoundInward << 12)
        | (RemoveZero << 13)
        | (Uppercase << 20),
    )
