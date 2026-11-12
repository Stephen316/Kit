# File notice retirement

Kit no longer adds per-file license boilerplate.
The Python steering checks, generators, and CI no longer require or insert it.
All other CI and merge queue checks still apply.

Use the [standalone license](../../LICENSE) for the repository license.
The cleanup preserves separate attribution records and third-party license text.
The [standards manifest](../../.agents/skills/standard-pr-practice/references/Standards/Manifest.json)
links to the original records in Git history.

The [queue guide](../../MergeQueue.md) describes the remaining checks.
Static inspection checked the tracked text for the retired boilerplate.
Remote CI verifies steering, generators, and queue policy.
