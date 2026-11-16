from dataclasses import dataclass as Dataclass
from pathlib import PureWindowsPath
from struct import pack as PackFields, unpack as UnpackFields

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

KDefaultMaterialAsset = ("data", "graphics", "materials", "color.p2m")
KDefaultShader = "defaultplastic"
KRecordedBump = UnpackFields("<f", PackFields("<f", 0.001))[0]


@Dataclass(frozen=True, slots=True)
class CmgrVisualFields:
    SurfaceColor: int
    WireColor: int
    HiddenLineColor: int
    MaterialName: str
    AppearanceId: int
    MaterialColor: int
    NativeAssetPath: str
    MappingMode: int
    BumpStrength: float
    DisplacementDistance: float
    UsesNormalMap: bool
    UsesDefaultAppearance: bool


def RequireVisualFields(Generation: int, Fields: CmgrVisualFields) -> None:
    RequireArch(Generation, 19000, "CMgr visual prefix generation")
    Colors = (
        Fields.SurfaceColor,
        Fields.WireColor,
        Fields.HiddenLineColor,
        Fields.MaterialColor,
    )
    RequireArch(
        all(0 <= Color <= 0xFFFFFF for Color in Colors),
        True,
        "CMgr packed visual colors",
    )
    RequireArch(
        0 < Fields.AppearanceId < 1 << 64,
        True,
        "CMgr allocated PW material appearance ID",
    )
    RequireArch(Fields.MaterialName, "Steel", "CMgr ordinary ID name")
    RequireArch(
        (Fields.MappingMode, Fields.UsesNormalMap, Fields.UsesDefaultAppearance),
        (3, True, True),
        "CMgr ordinary RealView and default appearance modes",
    )
    RequireArch(
        all(
            Value in (0.001, KRecordedBump)
            for Value in (Fields.BumpStrength, Fields.DisplacementDistance)
        ),
        True,
        "CMgr retained bump and displacement settings",
    )
    Locator = PureWindowsPath(Fields.NativeAssetPath)
    RequireArch(
        (
            Locator.is_absolute(),
            ".." in Locator.parts,
            any(ord(Char) < 32 for Char in Fields.NativeAssetPath),
            tuple(Part.casefold() for Part in Locator.parts[-4:]),
        ),
        (True, False, False, KDefaultMaterialAsset),
        "CMgr installed default material locator",
    )


# The filename is supplied by the document's target installation.
def WriteRealView(Writer: ArchiveWriter, Fields: CmgrVisualFields) -> None:
    Writer.raw(PackFields("<Q", Fields.AppearanceId))
    Writer.string(KDefaultShader)
    Writer.raw(PackFields("<BI", Fields.MappingMode, Fields.MaterialColor))
    # Mapping basis, origin, face width and the single color form.
    Writer.raw(PackFields("<10fi", 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1))
    # Reflectivity, color mix, three original-term sentinels and illumination axes.
    Writer.raw(PackFields("<5fi2f", 0.05, 0, -1, -1, -1, 0, 0, 0))
    Writer.string(Fields.NativeAssetPath)
    Writer.raw(PackFields("<I2f", 0xFFFFFF, 0.6, 1))
    Writer.string("")
    # Double-sided surface and the caller's custom bump convention.
    SurfaceFlags = 0x40 | (0x100 * Fields.UsesNormalMap)
    Writer.raw(
        PackFields(
            "<3fifi",
            Fields.BumpStrength,
            Fields.DisplacementDistance,
            0,
            SurfaceFlags,
            0,
            0,
        )
    )
    Writer.raw(PackFields("<13f", 1, 0, 0, 0, 1, 0, 0, 0, 1, 90, 1, -1, -1))
    Writer.string("")
    Writer.raw(PackFields("<f", 0))


# The body is inline in the already-open visual object and ends at the DSPBR body.
def WriteCmgrVisualPrefix(
    Writer: ArchiveWriter, Generation: int, Fields: CmgrVisualFields
) -> None:
    RequireVisualFields(Generation, Fields)
    Writer.raw(
        PackFields("<3I", Fields.SurfaceColor, Fields.WireColor, Fields.HiddenLineColor)
    )
    Writer.string("")
    Writer.string(Fields.MaterialName)
    # Ambient, diffuse, specular, shininess, transparency, emission and absent texture.
    Writer.raw(PackFields("<6di", 1, 1, 0.5, 0.3125, 0, 0, 0))
    Writer.raw(PackFields("<5i", 1, 0, 1, 1, 1))
    Writer.string("")
    Writer.raw(PackFields("<2i", 1, 1))
    WriteRealView(Writer, Fields)
    # Empty PLM identifier, absent secondary texture and empty material map.
    Writer.string("")
    Writer.raw(PackFields("<2i", 0, 0))
    # Empty add-in identifier, lightweight rendering and unnamed appearance.
    Writer.string("")
    Writer.raw(PackFields("<2i", 0, 1))
    Writer.string("")
    Writer.raw(PackFields("<6i", 0, Fields.UsesDefaultAppearance, -1, 0, 0, 1))
