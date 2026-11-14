# Parallel research sessions and model runners design

## Behavior and scope

Adds a [design](../../Reference/Research/ParallelSessions.md) for many concurrent research sessions on one machine.
A supervisor claims jobs through a controller interface, runs registered runners in separate pools and finishes each job.
A03 is the first controller adapter; another controller can replace it when it keeps the same guarantees.
Pool capacity uses CPU, memory, controller, provider and resource limits, an adaptive start and a calibration command.
Up to 20 small decode jobs can share one session, with a separate lease and result for each job.
A Codex runner executes optional model investigations through `codex exec` with a sandbox, an output schema and an event stream.
A Claude runner uses the Messages API without tools for hypotheses and Claude Code in a disposable worktree for candidate patches.
Each runner uses one fixed model at two efforts: `claude-opus-5-5` and `gpt-6.1-sol`, at `medium` first and `xhigh` only after a model failure.
A question that fails both steps is parked.
After two first-step failures with the same signature, later questions with that route key start at `xhigh`.
The design has no ranking set, ranked ladder or automatic model replacement.
A use report records attempts, passes and tokens for each step without changing the models.
The Codex and Claude error tables separate model failures from infrastructure failures.
A stable packet prefix lets both providers reuse cached input.

## Usage and limits

This is a design only; no code, command or controller schema change is added.
The proposed child steps A08a, A08b, A10a, A10b, A10c, A10d and A15a require an explicit request and a claim.
The fixed model pairs replace the earlier ranked ladders by operator decision.
Model-run commands inside the Codex sandbox need explicit approval as an exception to the current plan rule.
The private data boundary for the Codex runner needs verification before external transmission.

## Verification evidence

Source review checked the A03 command interface, claim logic, resource behavior and the installed `codex exec` options.
Codex model descriptions come from the local model list; Claude prices come from the cached Anthropic price table.
No local tests, Codex sessions or calibration runs were executed.
