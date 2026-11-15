# The bundled SOLIDWORKS example has unqualified sketch support

## Expectation

The historical `re/solidworks/examples/.SLDPRT/example.SLDPRT` fixture can appear suitable for every successful native-to-JSON writer check.
Earlier structural decoding and serialization checks did not establish complete sketch support semantics.

## Observed behavior

The [remote job](https://github.com/TryUniCAD/Kit/actions/runs/43665357887/job/132663393914) tested revision `3a432ea0d732186f6df4ae074f0fc7d91765faa9`.
The strengthened support assertion failed for the bundled example.
The public conversion failure identified unqualified support evidence for `sldprt:sketch:40`.
The new support guard correctly refused export. The positive fixture expectation was wrong.

## Workaround

Keep the original native fixture and its unresolved evidence unchanged.
Use it to verify direct JSON export refusal and destination preservation.
Use an independently authored Fusion file for the positive direct JSON boundary check.
Use the same independent source for generic bridge and carrier policy cases.
Registry staging cases can use its typed neutral serialization while retaining their output and rollback assertions.
Keep the P04 native equation text and dependency checks independent from support qualification.
Require export refusal while P04 support evidence remains unqualified, even when both formulas have resolved dependencies.
Do not replace fallback classifications with `plane-reference` to make an export pass.

See [the support write gate](../../Changes/Research/SolidWorksSupportWriteGate.md) for the behavior and remaining evidence requirements.
