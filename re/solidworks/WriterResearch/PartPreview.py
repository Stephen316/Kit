# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Render fresh ordinary part preview pixels from an authored rectangle."""

from dataclasses import dataclass
from math import ceil, floor, isfinite, sqrt

from HeaderTail import Point
from PartFraming import VersionStorage
from PrincipalPlaneView import KPrincipalFrames, PlanePoint
from RectangleCorners import ContourPairs, CornerPoint
from RectangleSupport import KProfileAxes

# the ordinary members use independent raster canvases
DIB_SIZE = (1420, 710)
PNG_SIZE = (640, 480)

# a positive world octant camera sees the maximum coordinate face on each axis
CAMERA_U = (1 / sqrt(2), -1 / sqrt(2), 0.0)
CAMERA_V = (1 / sqrt(6), 1 / sqrt(6), -2 / sqrt(6))

# the rgb colors belong to the preview caller's presentation policy
Rgb = tuple[int, int, int]
Palette = tuple[Rgb, Rgb, Rgb]
WorldFace = tuple[Point, Point, Point, Point]
Pixel = tuple[int, int]
PixelFace = tuple[Pixel, Pixel, Pixel, Pixel]


# the base stays as a stable viewport anchor for forward and reversed extrusions
@dataclass(frozen=True, slots=True)
class PreviewDrawing:
    Base: WorldFace
    Faces: tuple[WorldFace, ...]
    Solid: bool


# the complete authored edge loop must resolve before we add an optional swept cap
def BuildPreviewDrawing(
    DatumId: int,
    Corners: tuple[CornerPoint, ...],
    Edges: dict[int, tuple[int, int]],
    SignedDepthMetres: float | None,
) -> PreviewDrawing:
    if type(DatumId) is not int or DatumId not in KProfileAxes:
        raise ValueError("unsupported ordinary preview datum")
    ContourPairs(Corners, Edges)
    LowU, HighU = sorted({Corner.Position[0] for Corner in Corners})
    LowV, HighV = sorted({Corner.Position[1] for Corner in Corners})
    Frame = KPrincipalFrames[DatumId - 2]
    Base = (
        PlanePoint(Frame, LowU, LowV),
        PlanePoint(Frame, HighU, LowV),
        PlanePoint(Frame, HighU, HighV),
        PlanePoint(Frame, LowU, HighV),
    )
    if SignedDepthMetres is None:
        return PreviewDrawing(Base, (Base,), False)
    if (
        type(SignedDepthMetres) not in (int, float)
        or not isfinite(SignedDepthMetres)
        or not SignedDepthMetres
    ):
        raise ValueError("ordinary preview requires a finite nonzero signed sweep")
    X, Y, Z = (Coordinate * SignedDepthMetres for Coordinate in Frame.Normal)
    A, B, C, D = ((U + X, V + Y, W + Z) for U, V, W in Base)
    Cap = (A, B, C, D)
    Low, High = (Base, Cap) if SignedDepthMetres > 0 else (Cap, Base)
    U0, U1 = (1, 2) if Frame.USign > 0 else (3, 0)
    V0, V1 = (2, 3) if Frame.VSign > 0 else (0, 1)
    return PreviewDrawing(
        Base,
        (
            High,
            (Low[U0], Low[U1], High[U1], High[U0]),
            (Low[V0], Low[V1], High[V1], High[V0]),
        ),
        True,
    )


# projection replaces any native camera style with a fixed orthographic world view
def ProjectPoint(Vertex: Point) -> tuple[float, float]:
    return (
        sum(Value * Axis for Value, Axis in zip(Vertex, CAMERA_U, strict=True)),
        sum(Value * Axis for Value, Axis in zip(Vertex, CAMERA_V, strict=True)),
    )


# one scale preserves shape proportions while centering the actual unswept profile
def FitFaces(Drawing: PreviewDrawing, Width: int, Height: int) -> tuple[PixelFace, ...]:
    Base = tuple(map(ProjectPoint, Drawing.Base))
    CenterX = sum(X for X, _ in Base) / 4
    CenterY = sum(Y for _, Y in Base) / 4
    Faces = tuple(tuple(map(ProjectPoint, Face)) for Face in Drawing.Faces)
    Radius = max(
        max(abs(X - CenterX) / Width, abs(Y - CenterY) / Height)
        for Face in Faces
        for X, Y in Face
    )
    if not isfinite(Radius) or Radius <= 0.0:
        raise ValueError("invalid projected preview extent")
    Scale = 0.40 / Radius
    if not isfinite(Scale):
        raise ValueError("projected preview extent is too small")

    # a fixed fit puts both source and generated faces on a common pixel grid
    def FitFace(Face: tuple[tuple[float, float], ...]) -> PixelFace:
        A, B, C, D = (
            (
                round(Width / 2 + (X - CenterX) * Scale),
                round(Height / 2 + (Y - CenterY) * Scale),
            )
            for X, Y in Face
        )
        return A, B, C, D

    return tuple(map(FitFace, Faces))


# scanline intersections fill each convex visible face without gap or hidden geometry
def FillFace(Pixels: bytearray, Width: int, Face: PixelFace) -> None:
    Edges = tuple(zip(Face, (*Face[1:], Face[0]), strict=True))
    Rows = tuple(Y for _, Y in Face)
    if len(set(Face)) != 4 or min(Rows) == max(Rows):
        raise ValueError("projected face does not survive rasterization")
    for Row in range(min(Rows), max(Rows)):
        ScanY = Row + 0.5
        Crossing = sorted(
            X0 + (ScanY - Y0) * (X1 - X0) / (Y1 - Y0)
            for (X0, Y0), (X1, Y1) in Edges
            if min(Y0, Y1) <= ScanY < max(Y0, Y1)
        )
        if len(Crossing) != 2:
            raise ValueError("projected face has an invalid scanline")
        Left, Right = Crossing
        Start = Row * Width + ceil(Left - 0.5)
        Stop = Row * Width + floor(Right - 0.5) + 1
        Pixels[Start:Stop] = bytes((2,)) * (Stop - Start)


# outlining each visible polygon after its fill retains the authored edges
def DrawEdge(Pixels: bytearray, Width: int, First: Pixel, Last: Pixel) -> None:
    X, Y = First
    EndX, EndY = Last
    DeltaX, DeltaY = EndX - X, EndY - Y
    Steps = max(abs(DeltaX), abs(DeltaY))
    if Steps == 0:
        raise ValueError("projected edge does not survive rasterization")
    for Step in range(Steps + 1):
        Column = round(X + Step * DeltaX / Steps)
        Row = round(Y + Step * DeltaY / Steps)
        Pixels[Row * Width + Column] = 1


# drawing and encoding use one indexed pixel contract for both member sizes
def DrawPreview(Drawing: PreviewDrawing, Width: int, Height: int) -> bytes:
    if (
        type(Width) is not int
        or type(Height) is not int
        or (Width, Height) not in (DIB_SIZE, PNG_SIZE)
    ):
        raise ValueError("unsupported ordinary preview canvas")
    Faces = FitFaces(Drawing, Width, Height)
    Pixels = bytearray(Width * Height)
    if Drawing.Solid:
        for Face in Faces:
            FillFace(Pixels, Width, Face)
    for Face in Faces:
        for First, Last in zip(Face, (*Face[1:], Face[0]), strict=True):
            DrawEdge(Pixels, Width, First, Last)
    return bytes(Pixels)


# rgb inputs define three visible values shared by both encoders
def ValidatePalette(Colors: Palette) -> None:
    if (
        len(Colors) != 3
        or len(set(Colors)) != 3
        or any(
            len(Color) != 3
            or any(type(C) is not int or not 0 <= C <= 255 for C in Color)
            for Color in Colors
        )
    ):
        raise ValueError(
            "preview requires distinct byte RGB background, outline and fill"
        )


# the two wrappers use different color representations of the fresh drawing
@dataclass(frozen=True, slots=True)
class PreviewRasters:
    DibIndices: bytes
    PngRgba: bytes


# the caller supplies all presentation colors independently of the source archive
def RenderPartPreview(
    Generation: int, Drawing: PreviewDrawing, Colors: Palette
) -> PreviewRasters:
    VersionStorage(Generation)
    ValidatePalette(Colors)
    Indices = DrawPreview(Drawing, *DIB_SIZE)
    ColorBytes = tuple(bytes((*Color, 255)) for Color in Colors)
    Rgba = b"".join(ColorBytes[Index] for Index in DrawPreview(Drawing, *PNG_SIZE))
    return PreviewRasters(Indices, Rgba)
