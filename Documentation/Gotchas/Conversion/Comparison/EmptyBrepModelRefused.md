# An empty B-rep model fails document validation

## Expectation

A comparator fixture can retain an unsupported B-rep domain and require an unresolved observation.

## Observed behavior

`BrepModel()` contains no bodies and fails the existing document validator before comparison.
Each B-rep body must also reference region, wire or vertex content.
The [body validator](../../../../src/interchange/brep/Validation/BrepBodyValidate.py) enforces both requirements.
The initial unsupported-domain fixture used an invalid empty model.

## Workaround

Supply an independently authored vertex and a body that references it.
Resolve `design_body_id` when that optional link is present.
Keep the existing document-validation boundary and the required unresolved comparison result.
The fixture supplies model-validation evidence only; native interpretation and conversion remain unqualified.

The corrected process fixture is in [SemanticDocuments.py](../../../../tests/Research/Archives/Comparison/SemanticDocuments.py).
It was reviewed against the validator without running local tests.
Hosted execution remains required.
