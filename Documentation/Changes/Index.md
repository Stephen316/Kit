# Documentation entries

[Browse change entries](./).
In a checkout, look for the relevant files under `Documentation/Changes/`.

Each repository addition requires a new PascalCase Markdown entry in the same PR.
Choose a filename that describes the specific change.
Use focused subdirectories as needed to stay within the repository path limit.
Describe behavior, usage, limits, and actual verification evidence.
Update the affected guide and link the entry directly in the PR.
The directory listings include new entries automatically.

Historical entries describe behavior and evidence at the time of their change.
They do not establish the current CI, deployment, or publication state.
Record later behavior in a new entry and the current guide.
Correct an existing entry if it misstates the original change or its evidence.
Pure documentation corrections can update their existing entry.
- [File notice retirement](FileNoticeRetirement.md)
