set -euo pipefail

RootPath=$(git rev-parse --show-toplevel)
GuardPath="$RootPath/.github/scripts/CheckBinaries.sh"
ScratchPath=$(mktemp -d)
trap 'rm -rf -- "$ScratchPath"' EXIT
export GIT_INDEX_FILE="$ScratchPath/Index"
git -C "$RootPath" read-tree --empty
BlobHash=$(git -C "$RootPath" hash-object -w --stdin < /dev/null)

for PathName in README.md re/Part.SLDPRT re/Model.f3d Documentation/Module.dll.md assets.dmg/Notes.md; do
  git -C "$RootPath" update-index --add --cacheinfo "100644,$BlobHash,$PathName"
done
bash "$GuardPath" "$RootPath"
CleanTree=$(git -C "$RootPath" write-tree)
BaseCommit=$(git -C "$RootPath" -c user.name='Binary guard CI' -c user.email=guard@example.invalid \
  commit-tree "$CleanTree" -m 'clean fixture')

for PathName in Module.dll Installer.DMG src/Module.DlL 're/Fusion/Client Downloader.dMg' $'re/line\nbreak.dll'; do
  git -C "$RootPath" update-index --add --cacheinfo "100644,$BlobHash,$PathName"
done
BinaryTree=$(git -C "$RootPath" write-tree)
BinaryCommit=$(git -C "$RootPath" -c user.name='Binary guard CI' -c user.email=guard@example.invalid \
  commit-tree "$BinaryTree" -p "$BaseCommit" -m 'synthetic prohibited paths')

if bash "$GuardPath" "$RootPath" > "$ScratchPath/Report" 2>&1; then
  printf 'guard accepted prohibited tracked paths\n' >&2
  exit 1
else
  ExitCode=$?
fi
[ "$ExitCode" -eq 1 ]
ReportText=$(cat "$ScratchPath/Report")

for PathName in Module.dll Installer.DMG src/Module.DlL 're/Fusion/Client Downloader.dMg' $'re/line\nbreak.dll'; do
  printf -v ExpectedLine 'prohibited binary path: %q' "$PathName"
  [[ "$ReportText" == *"$ExpectedLine"* ]]
  git -C "$RootPath" update-index --force-remove -- "$PathName"
done
bash "$GuardPath" "$RootPath/re"

HeadCommit=$(git -C "$RootPath" -c user.name='Binary guard CI' -c user.email=guard@example.invalid \
  commit-tree "$CleanTree" -p "$BinaryCommit" -m 'remove synthetic prohibited paths')
if bash "$GuardPath" "$RootPath" "$BaseCommit" "$HeadCommit" > "$ScratchPath/Report" 2>&1; then
  printf 'guard accepted prohibited paths removed by a later commit\n' >&2
  exit 1
else
  ExitCode=$?
fi
[ "$ExitCode" -eq 1 ]
bash "$GuardPath" "$RootPath" "$HeadCommit" "$HeadCommit"

if bash "$GuardPath" "$ScratchPath" > "$ScratchPath/Report" 2>&1; then
  printf 'guard accepted a non-repository directory\n' >&2
  exit 1
else
  ExitCode=$?
fi
[ "$ExitCode" -eq 2 ]

if bash "$GuardPath" "$RootPath" missing-reference "$HeadCommit" > "$ScratchPath/Report" 2>&1; then
  printf 'guard accepted an invalid commit reference\n' >&2
  exit 1
else
  ExitCode=$?
fi
[ "$ExitCode" -eq 2 ]

printf 'binary guard process checks passed\n'
