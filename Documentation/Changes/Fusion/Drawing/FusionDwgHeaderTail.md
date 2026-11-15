# DWG header tail is a prohibited vendor integrity check

## Problem

A DWG header section ends with four 16-bit values that Fusion checks before it opens a drawing.
A save without them stalls the open in Fusion 2706.1.17 with no dialog, as the
[header tail gotcha](../../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingHeaderTail.md) recorded.
Kit's authored shell writes four placeholder values taken from the drawing's version GUID, so a DWG
that Kit authors does not open, and the header writer copied the values of a parsed save back
unchanged.

The values are one encrypted block: a 16-bit checksum of the header area, a product code, a writing
version code and a zero short, encrypted with Blowfish under a 16-byte constant from `libacdb`.
That makes them a vendor integrity check, not a document field.

## Change

Kit does not compute them.

The [Fusion donor ban](../../../../Documentation/Reference/Research/FusionDonorBan.md) requires
black-box experiments only, forbids disassembling or tracing Fusion or its libraries, and forbids
reproducing a vendor integrity or trust check. The rule that produces these values can only be found
and used against that prohibition, so the header writer keeps the placeholder tail and no product
code reproduces the check.

The finding is recorded in
[`re/Fusion/Reconstruction/Drawings/ThirdParty/HeaderTail`](../../../../re/Fusion/Reconstruction/Drawings/ThirdParty/HeaderTail/README.md),
together with the measured result, so that it is not rediscovered by the same means.

## Behavior

| Case                                | Before                | After                 |
| ----------------------------------- | --------------------- | --------------------- |
| Parse a Fusion save                 | header vars and frame | unchanged             |
| Write a parsed save                 | header tail copied    | unchanged             |
| Author a new DWG                    | version GUID shorts   | unchanged             |
| Open a Kit-authored DWG in Fusion   | stalls                | stalls                |

No reader, writer or author behavior changes. The header writer, the author shell and the authored
header tests keep their previous code and expectations.

## Verification

`src/` is unchanged by this entry except for the removal of an unreleased implementation, so the
previous evidence stands: the authored header tests pass, and the corpus saves parse and re-emit as
before.

Measured on this branch, with the shipped reader and writer:

| Check                                                    | Result          |
| -------------------------------------------------------- | --------------- |
| Fusion-saved DWG read and re-emitted byte-exactly         | 60 of 60        |
| Fusion-saved DWG header typed into parametric variables   | 60 of 60        |
| Fusion-saved F2D drawing document re-emitted byte-exactly | 248 of 248      |
| `tools.Donors.CheckReplays src`                           | no recorded payloads in 3078 files |

The DWG and F2D corpora are Fusion saves kept outside the repository, so these counts are research
measurements rather than a CI check. The reader is therefore lossless and parametric for every sample
that was available, and the writer emits no recorded payload.

The research record carries the measured numbers from the withdrawn implementation: 54 of 60 corpus
headers reproduced byte-exactly and a drawing with a computed tail opened in local Fusion 2706.1.17
and accepted a scaling edit. Those numbers describe the withdrawn code, not a shipped path.

## Limits

A DWG that Kit authors still does not open in Fusion, and this entry does not fix that.
Closing that gap needs either a document-level field that Fusion accepts in place of the check, or an
explicit decision to lift the prohibition on reproducing vendor integrity checks.
