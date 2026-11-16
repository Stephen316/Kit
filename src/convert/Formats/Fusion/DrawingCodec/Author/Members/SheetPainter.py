from convert.Formats.Fusion.ContainerCodec.Preview.EmitPreview import EmitPreview

# paper color must remain consistent across callers so sheet objects retain their intended document relationships
KPaperColor = b"\xff\xff\xff\xff"

# ink color must remain consistent across callers so sheet objects retain their intended document relationships
KInkColor = b"\x40\x40\x40\xff"

# clear color must remain consistent across callers so sheet objects retain their intended document relationships
KClearColor = b"\x00\x00\x00\x00"


# the sheet image contract needs a shared interpretation so sheet objects retain their intended document relationships
def SheetImage(Width: int, Height: int, Aspect: float) -> bytes:
    SheetHeight = min(Height, round(Width / Aspect))
    TopEdge = (Height - SheetHeight) // 2
    BottomEdge = TopEdge + SheetHeight
    Pixels = bytearray(KClearColor * (Width * Height))
    FillBoxMut(Pixels, Width, (0, TopEdge, Width, BottomEdge), KPaperColor)
    Margin = max(1, Width // 48)
    Inner = (Margin, TopEdge + Margin, Width - Margin, BottomEdge - Margin)
    FrameBoxMut(Pixels, Width, Inner, KInkColor)
    TitleWidth = (Inner[2] - Inner[0]) * 3 // 7
    TitleHeight = max(2, (Inner[3] - Inner[1]) // 8)
    Title = (Inner[2] - TitleWidth, Inner[3] - TitleHeight, Inner[2], Inner[3])
    FrameBoxMut(Pixels, Width, Title, KInkColor)
    return EmitPreview(Width, Height, bytes(Pixels))


# the fill box contract needs a shared interpretation so sheet objects retain their intended document relationships
def FillBoxMut(
    Pixels: bytearray, Width: int, BoxValue: tuple[int, int, int, int], Color: bytes
) -> None:
    LeftEdge, TopEdge, RightEdge, BottomEdge = BoxValue
    SpanWidth = RightEdge - LeftEdge
    for RowIndex in range(TopEdge, BottomEdge):
        Start = (RowIndex * Width + LeftEdge) * 4
        Pixels[Start : Start + SpanWidth * 4] = Color * SpanWidth


# the frame box contract needs a shared interpretation so sheet objects retain their intended document relationships
def FrameBoxMut(
    Pixels: bytearray, Width: int, BoxValue: tuple[int, int, int, int], Color: bytes
) -> None:
    LeftEdge, TopEdge, RightEdge, BottomEdge = BoxValue
    for EdgeBox in (
        (LeftEdge, TopEdge, RightEdge, TopEdge + 1),
        (LeftEdge, BottomEdge - 1, RightEdge, BottomEdge),
        (LeftEdge, TopEdge, LeftEdge + 1, BottomEdge),
        (RightEdge - 1, TopEdge, RightEdge, BottomEdge),
    ):
        FillBoxMut(Pixels, Width, EdgeBox, Color)
