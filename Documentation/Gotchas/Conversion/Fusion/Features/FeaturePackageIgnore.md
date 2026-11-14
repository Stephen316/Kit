# A Parts package is silently ignored

## Expectation

A new production package named `Parts` appears in `git status` like any other new folder.

## Actual behavior

Line 1038 of `.gitignore` contains the Python packaging pattern `parts/`.
Git sets `core.ignorecase=true` on a case-insensitive file system, which is the macOS default.
With that setting, Git matches the pattern against a folder named `Parts`.

`git check-ignore -v src/convert/formats/Fusion/DocumentCodec/Parts/X.py` reports `.gitignore:1038:parts/`.
The package files do not appear as untracked files.
A commit can therefore omit the complete package while the local tree still imports it.

## Workaround

Name the feature package `PartFeatures`.
Before a commit, run `git check-ignore -v` on each new production folder.
Do not change the shared ignore rule only for this package.
