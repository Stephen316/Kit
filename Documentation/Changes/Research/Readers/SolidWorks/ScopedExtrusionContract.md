# Preserve authored scope in the neutral extrusion definition

The licensed SOLIDWORKS controls preserve different policies for All bodies and explicit A+B even though the measured geometry agrees. A resolved body set alone cannot represent that distinction. [Native observations](../../Workers/SolidWorks/ThroughAllScopeNativeEvidence.md)

`ScopedExtrusionFeature` wraps the existing extrusion definition on a `CadDocument` feature step. `scope_mode=all_applicable` carries an empty authored selection. `scope_mode=explicit` carries the ordered design body IDs chosen for the operation. Both modes carry the distinct body IDs observed to change. The document validator checks those references against its design bodies. Scope references use stable design body IDs that remain in the document.

Ordinary extrusion definitions retain their existing `ExtrusionFeature` JSON record. The scoped variant has its own `ScopedExtrusionFeature` wire tag, so a reader or writer must explicitly handle its policy to use it. This contract supports the known scope distinction. Bidirectional native acceptance remains separate.

Read-only verification passed all three scoped definitions through the JSON record encoding and decoding. The ordinary P04 through-all document retained the same 246,000-byte JSON with SHA-256 `c209f52d9eb3ead391f5cb8d65d63fca71fad254dff29fec10165a2cf32a84ff` before and after the type registration.
