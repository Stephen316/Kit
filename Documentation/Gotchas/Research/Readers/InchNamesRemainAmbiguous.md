# Inch scalar names remain ambiguous

## Expectation

A dictionary keyed by scalar name can appear to replace a complete named-scalar search without changing its meaning.

## Actual behavior

An owner can contain more than one scalar with the same name.
The inch binder requires exactly one same-name candidate before checking identity, role, and display rounding.
Keeping only the first or last scalar would silently convert ambiguous evidence into a resolved dimension.
Filtering candidates by rounded value before counting would change that same acceptance rule.

## Workaround

Index each owner independently and retain a tuple of all original candidates under each name.
Reject a tuple whose length is not one before applying the existing scalar proof checks.
Share that index while the owner tuple remains stable.
Do not cache it globally by a reusable object identifier.

See [the indexed-binding change entry](../../../Changes/Research/Readers/IndexedInchScalarBinding.md).
