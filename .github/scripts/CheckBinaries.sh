set -euo pipefail

if [ "$#" -gt 3 ] || [ "$#" -eq 2 ]; then
  printf 'usage: bash CheckBinaries.sh [repository [base head]]\n' >&2
  exit 2
fi

ListPath=$(mktemp)
CommitPath=$(mktemp)
trap 'rm -f -- "$ListPath" "$CommitPath"' EXIT
if ! git -C "${1:-.}" ls-files --cached --full-name -z -- ':(top)' > "$ListPath"; then
  printf 'unable to inspect the git index\n' >&2
  exit 2
fi

if [ "$#" -eq 3 ]; then
  if ! BaseCommit=$(git -C "$1" rev-parse --verify --end-of-options "$2^{commit}") ||
     ! HeadCommit=$(git -C "$1" rev-parse --verify --end-of-options "$3^{commit}") ||
     ! git -C "$1" rev-list "$BaseCommit..$HeadCommit" > "$CommitPath"; then
    printf 'unable to inspect the incoming commit range\n' >&2
    exit 2
  fi
  while IFS= read -r CommitHash; do
    if ! git -C "$1" diff-tree --root -m --no-commit-id --name-only --no-renames \
      --diff-filter=ACMT -r -z "$CommitHash" -- >> "$ListPath"; then
      printf 'unable to inspect an incoming commit\n' >&2
      exit 2
    fi
  done < "$CommitPath"
fi

ExitCode=0
while IFS= read -r -d '' PathName; do
  case "$PathName" in
    *.[dD][lL][lL]|*.[dD][mM][gG])
      printf 'prohibited binary path: %q\n' "$PathName" >&2
      ExitCode=1
      ;;
  esac
done < "$ListPath"

exit "$ExitCode"
