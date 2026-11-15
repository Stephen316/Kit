# Fusion canonicalizes cap declarations to G1CAPS

## Expectation

A Form that Kit writes with `G0CAPS` or `G2CAPS` should retain that declaration through Fusion import, editing, save, and reopen.
Without a distinction, cap metadata could appear to disappear inside Kit's writer.

## Actual behavior

Fusion canonicalizes both cap alternatives to `G1CAPS` before the first control-point edit and after save and reopen.
It preserves `star-smoothness` values 0, 1, and 2.
The behavior is identical for native controls and independently written Kit documents.
The [fresh-process lifecycle](../../../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/NativeAcceptance.json) records both declarations at every stage for every case.
Kit's preparation check proves that its emitted F3D still preserves the input declaration before Fusion reads it.
The cap solve and measured geometry are unchanged by this canonicalization.

## Workaround

Preserve declarations in `SurfaceHeader` when Kit reads and writes TSM and F3D directly.
Expect Fusion to canonicalize cap types to `G1CAPS` during its own native lifecycle.
Do not claim that the original cap declaration survives a Fusion save.
Compare the full geometry and star value instead.
Legacy swaps can continue to require identical declarations as a layout invariant.

## Evidence

- [Cap preparation](../../../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/Preparation.json)
- [Native lifecycle](../../../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/NativeAcceptance.json)
- [Integration coverage](../../../../../../tests/convert/formats/FusionCodec/Documents/Form/GeneralAcceptTests.py)
