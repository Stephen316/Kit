# Older CLI branches need rationale coverage after policy synchronization

The CLI branch originally followed a rule prohibiting added code comments.
Current main instead requires a purpose comment above every owned Python
declaration, lambda, and module binding, and checks the entire tracked source tree.
Synchronizing the branches therefore exposed 148 missing CLI and process-case
rationales, even though the functional repair touched only sketch history.

Follow the current repository rule when authorized by the user. Add specific
purpose comments without changing behavior or disabling the policy gate. Run
`python -m tools.steering.CheckRationaleComments` as a static policy check; it does
not run tests. See [the change entry](../../../Changes/Commands/CliRationaleCoverage.md).
