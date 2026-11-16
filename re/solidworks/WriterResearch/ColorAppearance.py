# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from struct import pack as PackFields
from struct import unpack as UnpackFields

from convert.adapters.solidworks.container.Archive import ArchiveError, EncodeString

# The color asset's IOR also supplies the post-reader's derived float.
KColorIor = 1.5


# The native color conversion and IOR transform round intermediates to float32.
def Float32(Value: float) -> float:
    return float(UnpackFields("<f", PackFields("<f", Value))[0])


# Mode 1 expands the visual COLORREF in red, green, blue order.
def ColorChannels(ColorValue: int) -> tuple[float, float, float]:
    Scale = Float32(1.0 / 255.0)
    return (
        Float32((ColorValue & 0xFF) * Scale),
        Float32(((ColorValue >> 8) & 0xFF) * Scale),
        Float32(((ColorValue >> 16) & 0xFF) * Scale),
    )


# The archive baseline carries the default untextured color asset in display mode 1.
def EncodeColorDspbr(Generation: int, ColorValue: int) -> bytes:
    # The supported body includes both of the measured versioned store blocks.
    if type(Generation) is not int or Generation != 19000:
        raise ArchiveError("the default color appearance requires generation 19000")
    # The measured RGB conversion uses the three color bytes of a plain COLORREF.
    if type(ColorValue) is not int or not 0 <= ColorValue <= 0xFFFFFF:
        raise ArchiveError(
            "the default appearance color must be an unsigned 24-bit RGB"
        )

    Channels = ColorChannels(ColorValue)
    IorRatio = Float32(Float32(KColorIor - 1.0) / Float32(KColorIor + 1.0))
    IorDerived = Float32(IorRatio * IorRatio)
    EmptyPath = EncodeString("")
    return b"".join(
        (
            PackFields(
                "<26fi18fi2f",
                *Channels,  # Albedo from the owning visual color.
                0.0,  # Metallic.
                0.2,  # Roughness.
                0.0,  # Anisotropy.
                0.0,  # Anisotropy rotation.
                0.0,  # Transparency.
                1.0,  # Cutout opacity for zero legacy transparency.
                0.0,  # Constructor displacement retained by an empty asset value.
                0.0,  # Flip-flop.
                KColorIor,
                IorDerived,
                1.0,  # Specular.
                1.0,
                1.0,
                1.0,  # Specular tint.
                0.5,  # Sheen roughness.
                0.0,
                0.0,
                0.0,  # Sheen color.
                0.0,  # Subsurface anisotropy.
                1.0,
                1.0,
                1.0,  # Emission color.
                0.0,  # Emission value.
                0,  # Emission energy normalization.
                0.0,  # Clearcoat.
                0.0,  # Clearcoat roughness.
                1.0,
                1.0,
                1.0,  # Flip-flop color.
                0.0,  # Flake coverage.
                0.0,  # Flake size.
                0.0,  # Flake roughness.
                1.0,
                1.0,
                1.0,  # Flake color.
                100000.0,  # Attenuation distance.
                *Channels,  # Attenuation color from the same visual owner.
                0.0,
                0.0,
                0.0,  # Subsurface color.
                1,  # Thin-walled flag, with transparency and bump-map bits clear.
                0.0,  # Translucency.
                0.0,  # Abbe number.
            ),
            EmptyPath * 4,  # Albedo, normal, roughness and cutout opacity textures.
            EncodeString("basic"),
            PackFields("<f", 1.0),  # Constructor RealView-to-DSPBR texture scale.
            EncodeString("2025x"),
            EmptyPath,  # Clearcoat normal.
            PackFields(
                "<i6f",
                0,  # Emission mode.
                0.0,  # Thin film.
                0.4,  # Thin-film thickness.
                1.3,  # Thin-film IOR.
                1.0,
                1.0,
                1.0,  # Translucency color.
            ),
            EmptyPath * 2,  # Displacement and thin-film thickness textures.
            PackFields(
                "<2f", 1.0, 1.0
            ),  # Default normal and clearcoat normal strengths.
            EmptyPath * 3,  # Metallic, transparency and emission color textures.
        )
    )
