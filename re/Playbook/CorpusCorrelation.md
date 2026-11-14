# Phase D — Corpus correlation

**Goal:** use the generated corpus, where every parameter, feature and value is already known, to
find where each one is stored, in what encoding, inside what record grammar, and with what
neighbouring bookkeeping. Then express that as a model that can both read and write the data, and
prove it on samples it never saw.

**Inputs:** the corpus and manifests from phase C, the noise-floor mask and stream inventory from
phase A, the field tables and key boundaries from phase B.
**Outputs:** a field map with confidence labels, an executable grammar (construct, Kaitai or Kit's
own model), prediction results on held-out samples, and recorded unknowns.

---

## 1. Normalise first

Every comparison in this phase runs on normalised streams, never on raw files.

1. Extract every stream or member (phase A container grammar).
2. Decompress every compressed layer. Record the compression parameters, but compare the
   decompressed bytes.
3. Mask the noise fields located by the control pairs (timestamps, GUIDs, session ids).
4. Split object-serialised streams into objects using the phase B read-object arithmetic or a
   runtime trace, so comparisons are per object, not per stream.
5. Store each normalised stream once, keyed by sample and stream name, in a columnar layout
   (`.rescratch/<vendor>/normalised/`). Every analysis below reads from there.

---

## 2. Known-value search

The fastest locator. For each parameter in a sample's manifest, enumerate every plausible encoding
and search the normalised streams for it.

### 2.1 Candidate encodings for a number

For a parameter with value _v_ (in API internal units) generate all of:

| family          | variants                                                                                              |
| --------------- | ----------------------------------------------------------------------------------------------------- |
| IEEE floats     | f64 LE, f64 BE, f32 LE, f32 BE                                                                        |
| units           | _v_ in metres, millimetres, centimetres, inches, feet; radians and degrees; and the user-facing value |
| scaled integers | round(_v_ × 10^k) as i16/i32/i64, LE/BE, for k = 0..9; fixed-point 16.16                              |
| variable length | ULEB128, SLEB128, zig-zag varints, protobuf-style varints                                             |
| text            | decimal strings with various precisions, exponent forms, the expression text (`12.3mm`, `12.3 mm`)    |
| derived         | 1/_v_, _v_², _v_/2 (radius vs diameter), 2π − _v_, π − _v_, −*v*                                      |
| packed          | the value inside a vector or matrix (search for neighbouring known coordinates in sequence)           |

Search each encoding in each stream. A hit in one sample is a coincidence until the same relative
location holds the corresponding value in every sample of the family.

```python
import struct

def encodings(v):
    out = {}
    for unit, k in (("m", 1.0), ("mm", 1e3), ("cm", 1e2), ("in", 1 / 0.0254)):
        x = v * k
        out[f"f64le:{unit}"] = struct.pack("<d", x)
        out[f"f64be:{unit}"] = struct.pack(">d", x)
        out[f"f32le:{unit}"] = struct.pack("<f", x)
        for p in range(0, 7):
            n = round(x * 10**p)
            if -2**31 <= n < 2**31:
                out[f"i32le:{unit}:e{p}"] = struct.pack("<i", n)
    return out

def find_all(stream, needle):
    i = stream.find(needle)
    while i != -1:
        yield i
        i = stream.find(needle, i + 1)
```

Floats are rarely exact after a unit conversion. For f64, also search with the last one or two
mantissa bytes wildcarded, then check the decoded value against _v_ with a relative tolerance of
about 1e-12. For f32, use about 1e-6.

### 2.2 Strings, names and enums

- Names in ASCII, UTF-8, UTF-16LE and UTF-16BE, with and without length prefixes (u8, u16, u32,
  varint; in bytes or in code units), with and without terminators.
- Localised names: the same feature in a localised install. Strings that change with locale but not
  with the model are display defaults, not data.
- Enums: the API integer value, and the value ±1 (zero- vs one-based), as u8/u16/i32.
- Booleans: a byte, a bit in a flags word (compare all bit positions across a boolean pair).

### 2.3 Geometry

- Points: search for the triple (_x_, _y_, _z_) as consecutive f64 values; sketch points may be
  2D in the sketch frame, not 3D in model space.
- Frames: a plane's placement as origin plus two or three unit vectors, or a 3×3/4×4 matrix in row-
  or column-major order. Search for the 1.0 and 0.0 patterns of the default planes first.
- Curves: a line as two points or point plus direction plus length; an arc as centre, radius, start
  and end angles or start/end/mid points; a spline as degree, knots, control points, weights.

---

## 3. Differential analysis within a family

When known-value search finds nothing (the value is transformed or derived) or finds too much, diff.

1. **One-factor ladders.** Align the normalised streams of consecutive samples. Bytes that change
   when exactly one parameter changes are candidates. Plot candidate bytes or decoded values against
   the parameter; a straight line is a direct encoding, a curve is a transform, steps are
   quantisation.
2. **Boolean pairs.** XOR the two streams. A single changed bit is a flag. A changed length means the
   flag adds or removes a record; the inserted span is the record.
3. **Enum sweeps.** For each enum value, record the changed span. Values that change only one field
   are simple enums; values that change the stream length add nested records. Cross-check with the
   phase B switch table.
4. **Count ladders.** Subtract stream _n_ from stream _n_+1. The difference is one repeated block
   plus the changed counts and lengths elsewhere. That gives you the block grammar, the counter
   fields and every length field that covers the block.
5. **Order permutations.** Reordering features exposes ordering indexes and dependency references:
   values that permute with the features.

When streams differ in length, align them rather than comparing offsets: sequence alignment
(`difflib.SequenceMatcher`, edlib, or Needleman–Wunsch on bytes) after object segmentation. Object-
level alignment is far more reliable than byte-level.

---

## 4. Statistical location

With hundreds of samples per family, let statistics find what eyes miss.

1. Build a matrix: rows are samples, columns are (stream, object type, field offset), values are the
   decoded candidates (as u8, u16, i32, f32, f64 at each offset). Use object-relative offsets once
   objects are segmented.
2. For each manifest parameter, compute the correlation (Pearson for linear, Spearman for monotone,
   mutual information for anything) between the parameter and every column.
3. Rank columns by score. The top hits are candidate locations. Verify each by decoding and comparing
   values, not by score alone.
4. For categorical parameters (enum, operation, topology), fit a shallow decision tree from columns
   to the parameter; the splits name the discriminating fields.
5. For derived fields, regress the column on several parameters (e.g. volume on depth × area). A good
   fit says "derived from these inputs". It does not give you a shippable rule; it tells you which
   loader code to read in phase B.

Statistics produce candidates. Only decoded agreement across the whole family, plus phase B evidence,
produces a finding.

---

## 5. Induce the grammar

As fields are located, write them into an executable grammar.

- **Tags and lengths.** Look for small integers before variable-length spans whose value equals the
  span length (in bytes, elements or code units), or the count of following items.
- **Type tags.** A value that is constant within one entity type and different between types is a
  tag. Cross-check with class ids from phase B.
- **Reference fields.** Values that equal another object's index or id. Build the reference graph
  and confirm that every reference resolves.
- **Optional fields.** Spans present in some samples and absent in others: tie each to the parameter
  or version that switches it.
- **Alignment and padding.** Zeros that bring records to 2/4/8-byte boundaries.

Write the grammar as Python `construct` or `dissect.cstruct` while iterating (easy to round-trip),
and as Kaitai `.ksy` or Kit's typed records once stable. Every field carries its confidence label
and evidence reference (see [Evidence.md](Evidence.md)).

**The reconciliation step.** For each field, put three sources side by side:

| source                | gives you                                  |
| --------------------- | ------------------------------------------ |
| phase B decompilation | order, type, width, version gate, domain   |
| phase D correlation   | location, encoding, meaning in model terms |
| phase C manifest      | the true value for every sample            |

Agreement of all three is _confirmed_. Disagreement is a finding: either the decompiled code is not
the code that runs, the corpus never exercised the branch, or the field is derived. Record which.

---

## 6. Predict, both ways, on held-out samples

A field map that only describes the samples it came from is a fit, not knowledge. Test it on the
held-out split.

1. **Parse prediction.** For each held-out sample, parse with the grammar and compare every decoded
   parameter with the manifest. Report agreement per field.
2. **Emit prediction.** For each held-out sample, take the manifest's model, emit the authored fields
   with the grammar, and compare with the sample's normalised stream. Report byte agreement per
   field, ignoring masked noise and fields you have proven derived.
3. **Round trip.** Parse a vendor file into the symbolic model, re-emit it, and compare byte for byte
   (see [WriterModel.md §2](WriterModel.md#2-the-byte-identity-gate)). This is the segmentation gate.

A field whose emit prediction fails on a held-out sample is not understood, however well it fits
the training samples. Find out why before moving on: usually an unexercised branch, a unit
conversion, a derived dependency, or a version gate.

---

## 7. Derived fields: never fit, always derive or prove optional

If a field correlates with authored parameters but is not one of them, it is derived. The
correlation tells you which inputs it depends on. It does not license shipping a fitted formula.

1. Find the loader or rebuild code that computes it (phase B, `trace_native_values` backwards from
   where it is written during save).
2. If the computation is a simple, explainable function (a count, a length, a bounding box, a sum),
   implement it from the model and confirm on held-out samples.
3. If the computation is a kernel operation (B-rep, tessellation, mass properties), prove with the
   deletion experiments from phase A that the app regenerates it, and emit nothing or a provably-valid
   empty.
4. If neither works yet, the field is an open question. Record it. Do not ship a fitted value, a
   table of observed values, or a copy from a sample.

---

## 8. Common traps

| trap                                                    | defence                                                                                   |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Coincidental hits for common values (0, 1, 0.01)        | Use distinctive values; require the hit at the same relative location in the whole family |
| Comparing raw compressed bytes                          | Always decompress and normalise first                                                     |
| Byte offsets drift when an earlier object grows         | Segment into objects; use object-relative offsets                                         |
| Value read back from the API differs from the value set | Use the read-back value as truth; record the difference as a boundary finding             |
| Units silently converted                                | Search every unit; include a 25.4 mm sample in every ladder                               |
| Two copies of the same value (authored and cached)      | Find both; establish which one the loader trusts with a stale-copy experiment             |
| A field that never varies in the corpus                 | It is not located, only observed. Add a family that varies it, or label it partial        |
| Uninitialised memory that looks like data               | It differs across control pairs with no parameter change; confirm in phase B              |
| Fitting the training samples                            | Hold out 20%; never look at held-out samples while deriving                               |
| Kit output mixed into the corpus                        | `"producer": "kit"` manifests in a separate tree; refuse them as inputs                   |

---

## 9. Exit criteria for phase D

- [ ] Every authored parameter in scope located, with encoding, units and record context.
- [ ] Grammar executable for every stream in scope, parsing the whole corpus without error.
- [ ] Each field reconciled against phase B and phase C, with a confidence label.
- [ ] Parse and emit predictions passing on the held-out split for every authored field.
- [ ] Derived fields identified, each with a derivation from loader evidence or a proof that the app
      regenerates it.
- [ ] Unknowns recorded with the family or trace that would resolve each.
