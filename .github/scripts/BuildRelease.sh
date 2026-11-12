#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

set -euo pipefail

ArchiveName="Kit-${GITHUB_SHA}"
mkdir -p "${RUNNER_TEMP}/source"
git archive --format=zip --prefix="${ArchiveName}/" --output="${RUNNER_TEMP}/source/${ArchiveName}.zip" "${GITHUB_SHA}"
git archive --format=tar --prefix="${ArchiveName}/" "${GITHUB_SHA}" | gzip -n > "${RUNNER_TEMP}/source/${ArchiveName}.tar.gz"
git show --no-patch --format=fuller --date=iso-strict "${GITHUB_SHA}" > "${RUNNER_TEMP}/CommitDetails.md"
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
    if grep -Eq "^${ArchiveName}/(re|examples/Fixtures/SolidWorks/donors)(/|$)" "${ContentsPath}"; then
      echo "Research or donor fixtures leaked into ${ContentsPath}" >&2
      exit 1
    fi
  done
)

SOURCE_DATE_EPOCH="$(git show -s --format=%ct "${GITHUB_SHA}")"
export SOURCE_DATE_EPOCH
uv build --no-sources --python 3.11 --out-dir "${RUNNER_TEMP}/distributions"

uv venv --python 3.11 "${RUNNER_TEMP}/ReleaseEnv"
PythonPath="${RUNNER_TEMP}/ReleaseEnv/bin/python"
uv pip install --python "${PythonPath}" --no-deps "${RUNNER_TEMP}"/distributions/*.whl
"${PythonPath}" -I -c 'from importlib.metadata import distribution; from convert import convert; import interchange; assert distribution("unicad-kit").entry_points["convert"].load() is convert'
PackageVersion="$("${PythonPath}" -I -c 'from importlib.metadata import version; print(version("unicad-kit"))')"
printf 'version=%s\n' "${PackageVersion}" >> "${GITHUB_OUTPUT}"
