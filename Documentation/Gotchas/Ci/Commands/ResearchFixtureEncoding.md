# Research JSON fixtures require encoding-independent reads

The pinned corpus manifest and research artifacts are UTF-8 JSON.
Reading them with `Path.read_text()` without an encoding can select the Windows process locale instead.
The manifest contains non-ASCII bytes, including a byte undefined in cp1252.
That can fail the fixture before the CLI behavior is exercised.

The compatibility suite reads JSON bytes directly and lets `json.loads` decode the JSON encoding.
Artifact equality still compares original bytes, and no interpreter locale or corpus content is changed.
Fixture JSON writes use the serializer's default ASCII escapes.

This was found during static review and confirmed by [Windows compatibility job 132624833489](https://github.com/TryUniCAD/Kit/actions/runs/43652831510/job/132624833489): five manifest fixture reads failed with a cp1252 decoding error while eleven process cases passed.
No local test ran.
Accepted-head execution evidence is recorded in the CLI PR.
