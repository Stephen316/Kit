# Platform cosine values differ in the last bit

## Expectation

The general cage rules take the cosine and sine of spoke angles 2πk/n. Python's `math.cos` and `math.sin` would give the same double on every platform. A Kit Form document would then have the same bytes on macOS and on Linux.

## Actual behavior

`math` calls the platform C library. The macOS library and glibc differ by one unit in the last place for some spoke angles.

| Valence n | Spoke k | Function | macOS minus correctly rounded |
| --- | --- | --- | --- |
| 3 | 1 | cosine | 5.6e-17 |
| 5 | 3 | cosine | -1.1e-16 |
| 6 | 2 | cosine | 5.6e-17 |
| 9 | 3 | cosine | 5.6e-17 |
| 10 | 6 | cosine | -1.1e-16 |
| 11 | 4 | cosine | 1.1e-16 |
| 11 | 10 | sine | 1.1e-16 |
| 12 | 4 | cosine | 5.6e-17 |
| 12 | 7 | sine | 5.6e-17 |

These are 9 of the 85 angles with n from 3 to 12. Every box cage has valence 3 corners. So seven `SwapFormCage` documents prepared on macOS had other SHA-256 values on the Linux runner.

The earlier stencil tables stored the cap rows as numbers, so their output used only exact float arithmetic. The general rules compute the rows, so they brought the platform library into the output.

## Workaround

`RoundTrig` computes the cosine and sine of the double angle with 90-digit `Decimal` arithmetic. It then rounds each result to the nearest double. `Decimal` is software arithmetic, so every platform gets the same bits. With it, macOS produced the seven swap documents with the Linux runner's digests. The cap rules call `RoundCosine` and `RoundSine` instead of `math.cos` and `math.sin`.

`math.sqrt`, `math.fsum` and the four basic operations are correctly rounded everywhere, so they need no change. `ClassifyEdges` still calls `math.atan2`. It compares the result with 1°. `CrossPlace` also bisects on that comparison to place a crease cut. A one-unit difference could move such a cut by one unit on another platform. No saved case has shown it, and the crease tests give the same results on both platforms.

## Evidence

- [General stencil swap preparation](../../../../../re/Fusion/LocalOracle/FormDocuments/StencilAccept/General/Preparation.json): all seven digests equal the Linux runner's digests.
- [General stencil swap acceptance](../../../../../re/Fusion/LocalOracle/FormDocuments/StencilAccept/General/NativeAcceptance.json)
- [Form documents](../../../../Changes/Fusion/TSpline/FusionFormDocuments.md)
