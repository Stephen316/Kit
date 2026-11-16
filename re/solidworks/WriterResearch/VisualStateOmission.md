# VisualStates omission path

The eight receipt-pinned P03 parts at capture revision
`466dcb172dfa3803463e07ccde963ba01671d200` are generation 19000. Each
contains the 1,789-byte `ThirdPtyStore/VisualStates` member. The following
loader and saver branches are static evidence from installed SOLIDWORKS
34.4.1.1011. Addresses are relative to the individual module image bases.
[P03 receipt](../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json)
[Current writer research](VisualStates.md)

| Module | Installed SHA-256 |
| --- | --- |
| `sldvisualstateu.dll` | `bcbe477995e6631e8b339f8ed043f6ef0b9c2450c5cce5c67cabeff27cb85e2a` |
| `sldprtu.dll` | `cb1e260f8411a39dc44f4d8a6255ea585c7a5e60b223d0e69d3f51a258ee96de` |
| `sldappu.dll` | `de39fa156eb9e92c030ec23c5d4a3a742aef941ec6246c7689c99ffb0abcd0b2` |

## Missing member and cached model state

The visual-state context constructor calls the load routine `0x7c9b0`
at `0x72c88`. The loader releases prior context-owned state if present
and clears its `+0x8` pointer at `0x7ca45–0x7ca59`. It tries the
`ThirdPtyStore` child at `0x7cb3b` and the `VisualStates` member at
`0x7cba9`. Failure to open the primary member reaches the
`VisualStates-Dev` fallback at `0x7cc15`. The null archive test at
`0x7cc60–0x7cc63` branches to `0x7cdf7`. This branch skips the stream
version, document flag and key-data pointer reads.

At `0x7cdf7–0x7ce31` the branch checks for a document, a successful
document virtual predicate at `+0x1250`, and zero from virtual
`+0xd0`. The primary `uiPartDoc_c` vtable at `sldprtu+0x1ff0f0`
binds the first predicate to the constant-true routine `0xa25b0`.
It binds `+0xd0` to the `uiBaseDoc_c::IsModified` import thunk
`0x19323d`. The implementation at `sldappu+0x2069d0` returns
document member `+0x90`. The part's virtual `+0xf88` retrieves the
configuration manager. The loader enumerates its configurations
at `0x7ce6a`, obtains each opened model at `0x7ce87`, and releases
and clears a non-null model `+0xd60` pointer at `0x7ce95–0x7ceb0`.
These predicates govern cache clearing. The absent archive path
then rejoins the common continuation at `0x7cee2`.

## Default representation

The common continuation requires a configuration manager at context
`+0x10` at `0x7cf57`. If the context's key data is absent, the
`0x7cf6b–0x7cf94` route allocates a `visStateKeyData_c` and constructs
it at `0x72cb0`. That constructor retains the manager at key data
`+0x58`, sets `+0x60` to 1 at `0x72ced`, initializes the representation
counter at `+0xb4` to zero at `0x72dba`, and creates a displayed-entity
tracker at `0x72e91`. No parsed sidecar version is needed for that
allocation. Further population checks key data `+0x60` and context
mode `+0x30` at `0x7cf98–0x7cfa7`.

The loader enumerates configurations at `0x7cfde` and moves the active
part configuration to the front at `0x7d027–0x7d038`. The separate
document-history helper `0x86840` exits the legacy migration path for
an applicable history version at least `0xf34`, using the comparison
at `0x868ea`. The common continuation can still build a representation
for a configuration. The checks at `0x7d34b–0x7d369` gate the
mode-1 call at `0x7d3a1`, which passes the current configuration
and its key data to builder `0x7e0b0`. The builder derives the first
representation number from the zero-initialized counter and obtains
the default display name from the actual configuration and localized
display-state name. The configuration-to-representation relation is
set at `0x7e7c7`. The receipt-pinned saved parts all carry configuration
0, representation 1 and `<Default>_Display State 1`.
[Representation and owner evidence](VisualStateOwners.md)

## Conditional save

The `VisualState_c` vtable at `0xd08d8` assigns its `+0xd8` slot
to save callback `0x81550`. The callback looks up the supplied
configuration manager in the live state map at `0x81584` through
`0x91480`. A match calls saver `0x81330` at `0x81594`. The callback
also returns 1 on the map-miss path, so its return alone cannot attest
that a stream was written.

The saver checks its configuration manager at `0x81346–0x8134d`.
It creates or opens `ThirdPtyStore` at `0x8140a` and the primary
`VisualStates` member at `0x81438`. A non-null archive from `0x81449`
allows the build's version, document flag and key-data pointer writes
at `0x814a9`, `0x814d1` and `0x814de`. The saver uses the current
live state and these storage results. The original member's presence
is outside these save predicates.

## Measurement scope

The historical generation-18000 matrix observed open, rebuild and
editable native history with `VisualStates` absent. The licensed
generation-19000 P03 omission campaign removed the partition,
lightweight data, display lists and ghost partition, while retaining
`VisualStates`. A separate generation-19000 witness must omit both
visual-state member names, preserve the remaining receipt-pinned
archive, and measure healthy controls around open, rebuild, a driving
dimension edit, save and fresh reopen. The comparisons need the active
display representation, material and visibility state, and feature
ownership. Inspection of the saved archive must separately establish
whether the primary member returned and whether its typed graph
preserves those roles. The static branch shows how reconstruction and
save can occur. Native equivalence remains unmeasured for this omission.
[Historical omission](../archive/Multistream.md#4-which-streams-are-load-critical)
[Licensed generation-19000 campaign](../../../Documentation/Changes/Research/Writers/SolidWorks/SolidWorksArchiveOmissions.md)

The private P03 omission plan `52ea7c63438e9830e8b323c3305956742cfe79a0e2b51902fbd411c0369c6fa2`
has a 32-member `VisualStates`-only omission and a 30-member omission that
also removes the previews. Both passed offline verification. The pinned parent contains no
`VisualStates-Dev` entry. These source-archive variants are ready for the
separately owned licensed run described above. The independently generated
preview-enabled Boss uses its own source, archive and measurement plan.
[Omission preparation receipt](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6924172379)
[Generated Boss witness](../../../Documentation/Changes/Research/Workers/SolidWorks/SolidWorksBossWitness.md)
