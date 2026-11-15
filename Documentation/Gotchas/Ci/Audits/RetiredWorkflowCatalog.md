# The workflow catalog can include retired files

## Expectation

An Actions catalog entry with `state: active` might appear to identify an available workflow on the default branch.

## Observed behavior

The repository catalog included workflow paths absent from the merged revision's Git tree.
The catalog state alone did not prove that their files or manual triggers still existed.

## Workaround

Verify the workflow file on the intended Git revision before selecting it for an audit.
Read its triggers and job conditions from that revision.
Use the current queue job inventory instead of a retired rehearsal entry.

The [workflow catalog API](https://docs.github.com/en/rest/actions/workflows#list-repository-workflows) returns metadata.
The Git tree establishes which files exist at the selected revision.
