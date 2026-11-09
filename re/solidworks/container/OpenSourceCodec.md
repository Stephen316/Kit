# Native stream codec repair

## Source audit

The implementation adapts the MIT-licensed openswx rotation codec at
`72291dc962bbf267fa40cd57813b273108ebac53`, and follows its payload-boundary
advancement and cache-cell recognition. Full attribution is shipped in
`src/convert/adapters/solidworks/container/OpenSwxLicense.md` and wheel license metadata.

The modern parser uses the file header's final byte as the name rotation key.
Version 4 is the familiar nibble swap; version 3 requires rotate-left by three
on read and rotate-right by three on write. Both local and central directory
names must use the selected version. A template-based rewrite now defaults to
the template version, while an explicit version still requests conversion.

Kit previously scanned inside accepted compressed payloads, allowing a complete
encoded record embedded in a stored DEFLATE block to become a sibling stream.
The scanner now advances to each accepted payload's end. It retains fail-closed
handling of genuinely ambiguous duplicate physical streams; neither upstream
nor this repair establishes authoritative active-directory selection for all
native container variants. In particular, the repository's real sample has
cache records and trailing container state, so treating every document as a
conventional ZIP with a terminal EOCD would be incorrect.

Cache cells have CRC-slot = twice logical size modulo 2^32, compressed-size-slot
= half logical size, and nonzero logical size. These are recognized separately from data records when bounded decoding
does not produce a valid stream. Valid compressed records take precedence over
the cache-cell heuristic. Recognized data records now reject truncated payloads, bad CRCs,
wrong decoded sizes, unfinished DEFLATE frames and trailing compressed bytes.
Inflation is bounded to advertised size plus one, with an aggregate decoded
size budget across accepted records.

## Candidates and limits

- openswx: MIT at the pinned commit above; native reader, no native writer.
- sldkit: legacy MIT commit `c43b5ef752a0e58535b7f8f744f7d7c68e3c0e90`;
  current new material at `6e50664343351e7c2c77844f2b839ddc5a8964b1` is
  PolyForm Noncommercial. It is not adopted as a runtime dependency.
- cadmpeg: Apache-2.0 code at `007eb640985bf34b8042591030c9891df5f8945f`;
  describes its SLDPRT support as L1 with partial semantic writing. Its directory
  and cache handling does not establish full native feature-history writing.

No examined candidate supplies a complete, vendor-verified, editable native
SOLIDWORKS writer. This change repairs the container codec, not every unsupported
feature family, drawing semantics, legacy OLE2 support, or unresolved geometry.
It does not claim vendor loadability or editable rebuild acceptance for new
feature families.

## Verification route

The same pinned openswx implementation also supplies the Parasolid section
grammar. `ReadParaSection.py` concatenates every length-prefixed zlib frame
within a declared section, including splits inside the `PS\0\0` signature.
Standalone wrappers and adjacent sections remain supported. Exact member
consumption, checksums, section bounds and a 2 GiB cumulative decoded-size
limit prevent silent truncation or partial geometry acceptance. Source spans
now include continuation headers and section padding. Damaged geometry raises
in strict reads and produces the existing diagnostic in permissive reads.

The semantic reader now retains a revolution axis's actual owning sketch in
its entity reference, direction selection and feature dependencies. The
checked-in socket-screw model uses Sketch1 as Revolve1's axis and Sketch3 as
its profile. Revolution reverse and symmetric direction remain unrecovered
and are not newly claimed as supported.

`NativeCodecTests.py` exercises the actual adapter and retained-source writer
using a real model's streams wrapped by an independent Python zipfile-based
fixture encoder. It covers versions 3 and 4, wire name encoding, version
preservation and override, embedded misleading records and damaged input.
The existing workflow quality job runs the complete SOLIDWORKS suite and
Parasolid format suite on the PR. Archived trace tests now locate their
checked-in renamed reports and resolve recorded Windows example paths against
the checkout. Missing untracked research corpora and the licensed Windows
application oracle are reported separately. CI also enforces the current no-added-comments instruction
while accepting retained legacy rationale comments; mandatory rationale
insertion was an obsolete, conflicting check. No tests are run locally. Full acceptance and the target
application oracle remain separate from the codec integration results.
