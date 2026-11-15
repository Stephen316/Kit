# Fusion directories cannot use ZIP method 93

Repacking a Fusion package with Zstandard for every ZIP entry can look like a valid way to exercise method 93 decoding.
The native container codec requires directory entries to be empty and either stored or deflated.
It rejects Zstandard directory entries even when file members are valid.

Preserve stored or deflated directory entries when repacking a package.
Use method 93 for file members only.
The CLI compatibility fixture now also asserts that every file member uses method 93.

This was observed in [Fusion compatibility run 43650183863](https://github.com/TryUniCAD/Kit/actions/runs/43650183863): one new fixture case failed while 2956 cases passed.
No decoder validation was relaxed and no local tests were run.
