#!/usr/bin/env bash
set -euo pipefail

if [[ "$(git rev-parse --is-shallow-repository)" != false ]]; then
  echo "Release version requires full Git history" >&2
  exit 1
fi
BaseVersion="$(uv version --short)"
if [[ ! "${BaseVersion}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Expected a three-part base version, got ${BaseVersion}" >&2
  exit 1
fi
CommitCount="$(git rev-list --first-parent --count "${GITHUB_SHA}")"
ReleaseVersion="${BaseVersion}.${CommitCount}"

ArchiveName="Kit-${GITHUB_SHA}"
mkdir -p "${RUNNER_TEMP}/source"
git archive --format=zip --prefix="${ArchiveName}/" --output="${RUNNER_TEMP}/source/${ArchiveName}.zip" "${GITHUB_SHA}"
git archive --format=tar --prefix="${ArchiveName}/" "${GITHUB_SHA}" | gzip -n > "${RUNNER_TEMP}/source/${ArchiveName}.tar.gz"
git show --no-patch --no-show-signature --format=%B "${GITHUB_SHA}" > "${RUNNER_TEMP}/ReleaseNotes.md"
(
  cd "${RUNNER_TEMP}/source"
  for ArchiveFile in "${ArchiveName}.zip" "${ArchiveName}.tar.gz"; do
    sha256sum -- "${ArchiveFile}" > "${ArchiveFile}.SHA256"
    sha512sum -- "${ArchiveFile}" > "${ArchiveFile}.SHA512"
    sha256sum --check -- "${ArchiveFile}.SHA256"
    sha512sum --check -- "${ArchiveFile}.SHA512"
  done
  unzip -tq "${ArchiveName}.zip"
  unzip -Z1 "${ArchiveName}.zip" > "${RUNNER_TEMP}/ZipContents.txt"
  tar --list --gzip --file "${ArchiveName}.tar.gz" > "${RUNNER_TEMP}/TarContents.txt"
  for ContentsPath in "${RUNNER_TEMP}/ZipContents.txt" "${RUNNER_TEMP}/TarContents.txt"; do
    grep -Fxq "${ArchiveName}/pyproject.toml" "${ContentsPath}"
    if grep -Eq "^${ArchiveName}/re(/|$)" "${ContentsPath}"; then
      echo "Research or donor fixtures leaked into ${ContentsPath}" >&2
      exit 1
    fi
  done
)

SOURCE_DATE_EPOCH="$(git show -s --format=%ct "${GITHUB_SHA}")"
export SOURCE_DATE_EPOCH
uv version --no-sync --python 3.11 "${ReleaseVersion}"
uv build --no-sources --python 3.11 --out-dir "${RUNNER_TEMP}/distributions"

uv venv --python 3.11 "${RUNNER_TEMP}/ReleaseEnv"
PythonPath="${RUNNER_TEMP}/ReleaseEnv/bin/python"
uv pip install --python "${PythonPath}" --no-deps "${RUNNER_TEMP}"/distributions/*.whl
"${PythonPath}" -I -c 'from importlib.metadata import distribution; from convert import convert; import interchange; assert distribution("unicad-kit").entry_points["convert"].load() is convert'
PackageVersion="$("${PythonPath}" -I -c 'from importlib.metadata import version; print(version("unicad-kit"))')"
if [[ "${PackageVersion}" != "${ReleaseVersion}" || ! -f "${RUNNER_TEMP}/distributions/unicad_kit-${ReleaseVersion}.tar.gz" ]]; then
  echo "Expected the installed wheel and source distribution to have version ${ReleaseVersion}" >&2
  exit 1
fi
printf 'Verified package version %s\n' "${PackageVersion}"
printf 'version=%s\n' "${PackageVersion}" >> "${GITHUB_OUTPUT}"
