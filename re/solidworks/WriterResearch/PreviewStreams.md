# Standalone part preview members

The eight generation-19000 P03 files at capture revision `466dcb172dfa3803463e07ccde963ba01671d200` retain two independently sized preview rasters. Replaying the native container and both image boundaries produced aggregate report SHA-256 `b62de7db1d97a7c6865032ffe456dc0cdf0f01de849cbae893a801c16eca694d`. [P03 receipt](../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json)

## Native wrappers

The installed SOLIDWORKS 34.4.1.1011 `sldmfcu.dll` has SHA-256 `bea7d36e54929371aa9d6db9faa3210b8661a14038eb1f0fcac714c6d110e9a6`. Its `suPreviewDIB_c::Serialize` at RVA `0x162550` chooses a representation from the format field at object `+0x10`. The legacy store sends the unsigned payload length at `0x162593` and writes the DIB through the byte writer at `0x1625bf`. Format 3 at `0x162589` calls `mfcut_serialiseToPNG`, which obtains the output file and passes the image from the input bitmap at `0x11aece–0x11af12`. The PNG branch writes a PNG datastream from byte zero.

`doccplu.dll` SHA-256 `120e1d5c359f5895d9785325995ebfaafc790ef7d74fe4fb0e242303f933939b` shows the configuration dependency on its preview path at RVA `0x2b480`. The routine reaches the source configuration, checks whether its preview is out of date, then calls `getConfigPreview` and `isValid` before serialization. If no image is available, control bypasses the preview write. The bitmap is supplied by configuration preview state. The wrapper derives its length from that image.

## Exact archive boundaries

| Member | Saved fields | Read-only P03 evidence |
| --- | --- | --- |
| `Preview` | Bytes 0–3 are the unsigned little-endian size of the remainder. Bytes 4–43 are a Windows `BITMAPINFOHEADER` with width 1420, height 710, one plane, 8 bits per pixel and `BI_RLE8`. The resolution and color-count words are zero. Bytes 44–1067 are 256 `RGBQUAD` entries. The RLE8 input begins at byte 1068. | All eight stored size fields match the complete extent and the header's image byte count. Each RLE stream produces 710 full bottom-up rows and reaches the end-of-bitmap escape at EOF. The palette's SHA-256 is `57a936dbacf1da3f6aec0001cdccf5f65844135bb4a616354a79b052b783819c` across all eight. Complete streams are 20,138–21,508 bytes. |
| `PreviewPNG` | Standard PNG signature at byte 0. `IHDR` at byte 8 specifies a 640 × 480 noninterlaced 8-bit RGBA image. `sRGB`, `gAMA` and `pHYs` follow at bytes 33, 46 and 62. The values are rendering intent 0, gamma 45455 and 3779 pixels per metre on each axis. A single `IDAT` starts at byte 83. | All chunks pass CRC verification and the last `IEND` ends at EOF. The zlib image stream expands to 480 rows of 2,561 bytes each, including a filter-0 prefix per row. Complete streams are 6,574–7,082 bytes. |

Both stored images change for the width, height and depth edits. Baselines A and B and the inch-unit capture are identical in each representation. The two different saved sizes and the raster changes make the bitmap and RGBA inputs separate authoring dependencies. A wrapper can consume independently rendered pixels and an indexed image, but the current rectangle-to-native route supplies no such images. Copying either saved image would retain the source preview.

The typed research wrappers take separate caller-owned index and RGBA arrays. They construct valid RLE8 runs and PNG scanlines, and do not depend on the vendor compressor's choice of packets. The hosted boundary verifies the saved streams separately from the generated wrapper round trip. [Writer](PartPreviews.py) [Archive verification](VerifyPartPreviews.py)

The bitmap layout and run semantics follow the Windows DIB rules. The second member uses standard PNG chunk framing. [Windows bitmap structure](https://learn.microsoft.com/en-us/windows/win32/gdi/bitmap-header-types) [Windows RLE8 rules](https://learn.microsoft.com/en-us/windows/win32/gdi/bitmap-compression) [PNG specification](https://www.w3.org/TR/png-3/)

## Omission candidate

The independent thumbnail reader in `sldmfcu` at RVA `0x9da30` attempts `PreviewPNG` at `0x9db5e` and falls back to `Preview` at `0x9dba5`. Its missing-member branch bypasses image deserialization. The configuration archive saves the missing and stale preview bits `0x100` and `0x80` set in the P03 files, even when both physical members are present. The separate configuration setters clear those bits only when an image is installed. [Configuration preview flags](CmgrMiddle.md#base-header)

Candidate verification would omit the two preview members together from an otherwise identical, receipt-bound P03 scratch copy, retain the measured configuration flags, and compare open, rebuild, dimension edit and fresh reopen with healthy before and after controls. The thumbnail result would be reported separately and a regenerated file would be checked for new members. The existing licensed omission campaign retained both previews. The native thumbnail fallback and complete saved wrapper evidence do not establish whole-document omission acceptance. [Existing licensed campaign](../../../Documentation/Changes/Research/Writers/SolidWorks/SolidWorksArchiveOmissions.md)
