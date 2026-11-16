# Explicit UTF-8 controller transport

The research controller now writes successful canonical JSON directly as UTF-8 bytes followed by one LF.
The paged event command uses the same transport.
Controller diagnostics, including argument-parser errors, are also encoded explicitly as UTF-8, preserving their existing text, truncation and exit codes.
The actual A03 adapter decodes both subprocess streams strictly as UTF-8 before applying its existing result and error handling.
Malformed successful JSON still fails parsing; invalid UTF-8 is not ignored or replaced.

The change prevents a locale-only encoding failure after a successful controller operation.
For example, a claim file containing a combining character can be written successfully and its lease committed before the acknowledgement reaches stdout.
The earlier text stream could then refuse that acknowledgement under an ASCII or incompatible Windows console encoding.
The job would already be running while the command reported failure.

Canonical JSON construction, the 1 MiB metadata limit, object and receipt digests, stored records, schema, transactions and operation return semantics are unchanged.
This repair does not make acknowledgement delivery transactional.
Broken pipes, process interruption and other I/O failures can still lose a response after commit.
The [output encoding gotcha](../../../Gotchas/Research/Workers/Controller/ControllerSuccessOutputEncoding.md) explains that boundary.

## Process coverage

New real-process coverage runs the controller CLI and actual A03 adapter with `PYTHONIOENCODING=ascii:strict`.
Each mode uses an isolated Unicode store and claim path, submits one job, obtains one usable lease, exercises a Unicode argument refusal and a real invalid-output refusal, renews that lease and completes the same attempt with a Unicode reason.
The CLI mode checks exact canonical UTF-8 bytes and one LF.
Both modes verify the stored result and receipt hashes, original Unicode values, artifact paths, completed state and exactly one attempt.
The paged event command is exercised separately through the same process boundary.

Pinned formatting, syntax compilation, type, steering, path, rationale, binary-range and whitespace checks validate the repair statically.
No local tests, collection, controller commands, adapter execution, reproductions or live-store operations were run.
Hosted process execution remains required.
The change establishes no CAD, capture or native-application acceptance.
