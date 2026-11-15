# Generation 19000 rectangle field synthesis

Native editable authoring remains open. This experiment matched 114 field spans in six P01 discovery archives.

Run `python re/solidworks/authoring/RectangleFields.py` from the checkout. The command reads the P01 SOLIDWORKS discovery set from Git revision `89c25945f5833ad9c3a1c6c683df510b5702dd54` and verifies the capture and authored specification pins. The independent fresh-process measurement receipt is `cea7ce1d29020a4102a134dd89695ddbdf58a7cd65373c3f579934c0400e67b5`. The observed build is `34.4.1.1011`. The compact report without its terminal newline has SHA-256 `ac9ec93027d38a2ffaa4c7e11619cf0fa80b16907c13d4d8c1ee375f23619ec1`.

## Field rules

The experiment builds a local graph from the API-observed directed perimeter, support frame, point operands and relation incidence. Three corner slots occur in the measured relation operands. The remaining slot resolves to the only perimeter endpoint outside that set. The Origin proxy stays distinct from its coincident corner. The graph supplies the reconstructed field values. The typed archive walk supplies the comparison boundaries. [Historical configuration and placement evidence](../../../Documentation/Changes/Research/Readers/SolidWorksRectangularPlaneEvidence.md)

| Loader evidence on the pinned build | Policy | Spans matched |
| --- | --- | ---: |
| `sgSketch` point and line dword count reads at `sldmodu+0x1451fc8` and `+0x14526ff` | Count the four corners and one proxy. Count the four perimeter members and one structural member. | 12 |
| Member dword relation-count storage at `sldmodu+0x1441db0` | Count measured point and line operands by native identity. Each corner and the proxy have point-specific incidences. | 54 |
| `sgPoint` 2D branch at `sldmodu+0x144e0ed` | Resolve model-space metres into the unit-scale sketch frame. Generate four pairs of little-endian doubles. | 24 |
| `sgCurve` reads at `sldmodu+0x144ecb3` and `+0x144ecf0` | Emit the directed corner slots for the four perimeter lines using short indices. | 24 |

The width and height edits move only their respective local coordinates. The inch-display case retains metre scalars. YZ exchanges the local axes and reverses one sign through the measured plane frame. The point slot and ordered perimeter references remain stable across these six controls. These fields are confirmed for this build and observed branch. The short-index escape and canonical allocation and traversal rules for arbitrary profiles still need their own evidence. [Member and loop reader evidence](../records/P04SketchGeometry.md#geometry-and-dimension-fields), [loader image pins](../records/P04ArchiveWalk.md#inputs)

## Remaining authoring boundary

The first physical corner starts at resolved byte 5,777 in these captures. At bytes 5,787–5,804 the member writes seventeen visual bytes through the helper at `sldmodu+0x100ef20`, before the relation count at 5,804. The member's explicit-width branch and the extra scalar fields after its pointer tables also need generation rules. The P01 controls share a single visual setup, so equality across them supplies no default or legal-range proof. Read the store branch of `sgMember` at `sldmodu+0x1441500` into the visual helper and width helper, then discriminate custom versus default display and width with one-factor controls. The first physical point also introduces the `sgLineHandle` class before later point rows refer to it. That allocation must come from the authored graph traversal. The external Origin proxy has its distinct `sgExtEnt_c` pointer at byte 6,486.

The first line spans 6,910–7,002. It has native ID −1, endpoints at slots 0 and 1, and curve contour word 0. The four independently measured perimeter lines have contour word 1. The former is a structural slot in this profile grammar. The flags and trailing words are reported observations. The current controls establish neither its complete neutral construction rule nor the direction-vector branch. The loader stores constructor state, display state and references that require their own proofs. [Curve base field names](../records/Sketch.md#2-fun_4c5d1b60--the-shared-curve-base-of-sgarc-and-sgline--partial)

The existing container codecs and archive map work can be advanced independently of this sketch-member boundary. Both must converge on a fully generated, editable profile, followed by fresh open, rebuild, driving-dimension edit and save/reopen between healthy controls. The discovery exercise provides no evidence for a loadable or usable generated part.
