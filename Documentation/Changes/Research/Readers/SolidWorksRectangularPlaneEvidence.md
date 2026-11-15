# SOLIDWORKS resolved rectangle planes

The research replay carries the configuration's class and object maps into `Contents/Config-0-ResolvedFeatures`. It reads the preceding principal planes and the origin profile before entering the actual `RectangleSketch` feature. After the line geometry and display records, it follows the typed `moCompRefPlane_c` to the earlier plane owned by the same part and decodes the enclosing profile placement. The zero-atom P01 and one-atom P03 branches each establish their map through the saved model structure.

Run the comparison from the repository root:

```shell
python re/solidworks/archive/RectangularPlaneEvidence.py > SolidWorksRectangularPlaneEvidence.json
```

The report pins capture revision `89c25945f5833ad9c3a1c6c683df510b5702dd54` and SHA-256 `0a6cd7d6fbca1adc66f24d3e9cbd856878f5f2d1b9c60d3accead5d2123b8434`. All six P01 and eight P03 parts agree with the clean reopens in an independent SOLIDWORKS `34.4.1.1011` process for plane, transform, four directed world-space perimeter lines and both named dimensions. Both YZ parts resolve to Right Plane. The others resolve to Front Plane. Perimeter comparison joins the saved segment ID to the measured ID and uses the specified absolute length tolerance of `0.000001` mm. P03 changes the stored member indices for two lines while retaining their native IDs.

Four additional licensed runs verified the decompressed streams and final configuration maps. Each replay reproduced all 75 live display pointer reads in order, including their stream offsets, counters and resolved types. The earlier loader traces identify the support class and placement field consumed at the end of the same profile. [Licensed loader observations](../../../../re/solidworks/records/PrincipalSupportCandidates.md#licensed-loader-observations)

| Control | Config pointer reads | Resolved pointer reads | Configuration map handoff | Normalized live witness SHA-256 |
| --- | ---: | ---: | ---: | --- |
| P01 baseline A | 121 | 325 | 106 | `06e3ac91e2dfbf6a5a9d23946b8564a0cca8a5a2431170318d5830c82ceb27c1` |
| P01 YZ | 121 | 325 | 106 | `e88a8985b66a699d929e7f5087b0a4f0bd675b93f0320c4b510b6e02db3419a1` |
| P03 baseline A | 129 | 449 | 111 | `2cda0743fbe1cadeaba28a6fbfc61c526bccc6ee202b795cf629e24b1578ec72` |
| P03 YZ | 129 | 449 | 111 | `249e1b02307ac25ac3d03a9639d39f6199b7a36df4ef8ccd6110e1efb684f4bf` |

## Profile return

Add `--through-profile` to read each rectangle's contour surface, saved file reference and four typed trim edges. The extended report SHA-256 is `8d3f9d7206e71876b2db8aa933a861029e4d1c6130851a59fb006f8dc8178aeb`. Each trim entry refers to the owning profile and materialized file reference. Its edge ID set matches the four saved lines. The P03 body chain also names those four edges.

All six P01 streams finish at the exact end of the resolved list with next map index 250. All eight P03 streams reach a schema-1 extrusion definition at map index 257. The licensed baseline and YZ controls independently confirm those boundaries and counters. P01 ends at 11,899 bytes in baseline A and 11,971 in YZ. The P03 extrusion starts at 11,996 in baseline A and 12,066 in YZ.

Production integration, P03 boss replay after the sketch, and editable conversion remain open.
