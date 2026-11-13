# Parallel research sessions design

## Behavior and scope

Adds a [design](../../Reference/Research/ParallelSessions.md) for many concurrent research sessions on one machine.
A supervisor claims jobs from the A03 controller, runs registered runners in separate pools and finishes each job.
Pool capacity uses CPU, memory, controller, provider and resource limits, an adaptive start and a calibration command.
A Codex runner executes optional model investigations through `codex exec` with a sandbox, an output schema and an event stream.
The tier selector, failure log and tier routes implement the plan's model escalation rule.
The Codex error table separates model failures from infrastructure failures.

## Usage and limits

This is a design only; no code, command or controller schema change is added.
The proposed child steps A08a, A08b, A10a, A10b and A15a require an explicit request and a claim.
Model-run commands inside the Codex sandbox need explicit approval as an exception to the current plan rule.
The private data boundary for the Codex runner needs verification before external transmission.

## Verification evidence

Source review checked the A03 command interface, claim logic, resource behavior and the installed `codex exec` options.
No local tests, Codex sessions or calibration runs were executed.
