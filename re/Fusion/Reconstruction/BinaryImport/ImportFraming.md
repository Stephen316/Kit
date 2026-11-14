# Independent ASM binary import framing

The independently authored cylinder SMB was valid without changing a byte. Its SHA-256 is `e543149d548412263728f3c33cabf115badbbc459d43e5a124a8df8f62d2e407`. Fusion 2706.1.17 accepted it through `TemporaryBRepManager.createFromFile`, produced the expected solid, and retained the measured geometry after a native F3D save and reopen.

This establishes native acceptance of the bounded analytic-cylinder SMB writer. The F3D archive in this acceptance sequence was authored by Fusion. This result does not establish an independently authored Fusion document, feature graph, body identity map, or parametric history.

## Why the first import route failed

`ImportManager.createSMTImportOptions` validates the extension as `.smt`. Supplying `.smb` fails option creation. Renaming binary bytes to `.smt` passes that extension check and sends the data through a text-oriented route. That failure was not evidence that the binary record stream was malformed.

The installed Python API documents `TemporaryBRepManager.createFromFile` as accepting SMT, SMB, SAT, and SAB at `Contents/Api/Python/packages/adsk/fusion.py:81145–81152`.

No extra standalone wrapper, compression, or embedded-record envelope was required. The same `ASM BinaryFile8` framing used by embedded Fusion SMB streams is accepted through the supported SMB route. The accepted standalone sample has no history partition or Fusion-specific body-map identity attributes.

## Header fields and unit semantics

The accepted binary begins with a 15-byte ASCII signature, followed by four signed integers in the width selected by that signature. `ASM BinaryFile8` uses eight-byte little-endian words here. The accepted values are `(23200, 0, 2, 2)`.

| Field | Accepted value |
| --- | --- |
| `save_format` | `23200` |
| `stored_record_count` | `0` |
| `top_level_entity_count` | `2` |
| `flags` | `2` |

The field names are research labels.
The accepted file has two top-level roots, the ASM header entity and the one body, which matches the third word.
Fusion accepted a stored record count of zero.
Earlier notes gave a restore-version formula built from `save_format` and `flags`, and a rule that bit 0 of `flags` does not prove history is absent.
Those rules came from binary inspection and are not confirmed by a black-box experiment.
The `232.5.0.65535` string in the ASM header record is the kernel build identity.

After the four words, the accepted file holds three strings and three real values in this order:

1. Product identity
2. Kernel/build provenance string
3. Timestamp string
4. Units metadata
5. Kernel absolute resolution
6. Kernel normal resolution

The independent writer uses this order and Fusion accepted it.
The resolution values are kernel metadata; their names do not establish millimeter units independently of the model coordinate convention.

The independent binary writes units metadata `10` and converts input millimeter coordinates to centimeters.
The accepted physical dimensions match this choice.
The standalone text writer instead writes metadata `1` and millimeter coordinates; these are two coherent unit representations, not different shapes.
Earlier notes said the import wrapper scales each body by `restored_units / 10`.
That rule came from binary inspection and is not confirmed by a black-box experiment beyond this one accepted case.

Eight-byte storage does not make all integer semantics unrestricted 64-bit values.
Earlier notes said readers reject eight-byte integers that differ from their sign-extended 32-bit value.
That rule is not confirmed by a black-box experiment.
The distinct `int64` token remains a separate type.

## Native acceptance evidence

The parent agent performed the native calls serially. The authoritative report is [BinaryTemporaryAcceptance.json](../../LocalOracle/Brep/BinaryTemporaryAcceptance.json).

| Measurement | Persistent body | Reopened native F3D |
| --- | --- | --- |
| Solid bodies | 1 | 1 |
| Faces / edges / vertices | 3 / 2 / 2 | 3 / 2 / 2 |
| Volume, cm³ | `7.7754418176350715` | `7.7754418176350715` |
| Center, cm | `(2.0000000001568523, -3.0000000000000004, 1.0500000000000003)` | Same |
| Minimum bounds, cm | `(0.5, -4.5, 0.5)` | Same |
| Maximum bounds, cm | `(3.5, -1.5, 1.6)` | Same |

The expected analytical center is `(2, -3, 1.05)` cm. The measured difference is numerical noise. The saved native F3D SHA-256 is `ce4ae6efcdb7814eb06284eb1b0eb3858bf80451fa3b13d31971676d11ce360c`.

The temporary body's `physicalProperties.centerOfMass` initially returned `(0, 0, 0)` despite correct volume and bounds. After the same body was added to a new direct-design document, the center was correct and remained correct after save/reopen. This is an observed context-dependent API result for this controlled case, not evidence that all temporary bodies always report an invalid center. Persistent-body measurements are required for this acceptance sequence.

## Acceptance route

The acceptance route is to retain the `.smb` extension, use `TemporaryBRepManager.createFromFile`, add the returned body to a fresh controlled direct design, inspect persistent geometry, and save/reopen through Fusion. No corrective binary mutation is supported or needed by the evidence. Independent generation of an embedded SMB payload is established for this analytic cylinder; independent assembly of the surrounding native Fusion document and parametric history remains separate work.
