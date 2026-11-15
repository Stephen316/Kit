# Reconstruct typed documents before asserting tuple fields

CadDocument JSON preserves tuple types with `$tuple` tags.
The `document` field in a neutral CLI inspection report retains that serialization.
Loading the outer report with `json.loads` does not turn tagged fields into plain Python tuples or lists.

Process tests now reconstruct `CadDocument` from that field before asserting typed assembly definitions, retained payloads, histories, and diagnostics.
The serialized artifact contract is unchanged.

[CLI process job 132643126381](https://github.com/TryUniCAD/Kit/actions/runs/43658760143/job/132643126381) reported six new fixture-assertion failures and 166 passing cases because raw tagged objects were treated as lists.
No local tests or decoding ran.
