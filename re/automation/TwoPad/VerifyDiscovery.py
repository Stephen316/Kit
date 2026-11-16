# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from argparse import ArgumentParser
from json import dumps as DumpJson
from pathlib import Path as FilePath
from subprocess import CalledProcessError
import sys

# the copyable verifier uses the source tree and the existing offline audit helpers
KRepository = FilePath(__file__).resolve().parents[3]
sys.path[:0] = [str(KRepository / "re" / "automation"), str(KRepository / "src")]

from PairedCaptureIntake import require as RequirePad
from PilotEvidence import pinned_record as ReadJsonPin

from PadArchive import CheckPadArchive
from PadGeometry import CheckControls, CheckEditGrid
from PadReceipts import CheckPhases, CheckSources


# the retained research package must reproduce each independently trusted digest
def AuditDiscovery(
    Directory: FilePath,
    RepoRoot: FilePath,
    Revision: str,
    ReportSha: str,
    AuthorSha: str,
    ReopenSha: str,
    StrictSdk: bool,
) -> dict:
    Directory = Directory.resolve(strict=True)
    RequirePad(Directory.is_dir(), "Expected the retained native run directory")
    Report = ReadJsonPin(Directory / "report.json", ReportSha)
    StockSha = CheckSources(RepoRoot, Revision, Report)
    Processes = CheckPhases(Directory, Report, AuthorSha, ReopenSha)
    Observations = Report["observations"]
    CheckControls(Directory, Observations, StockSha)
    Cases = Observations["cases"]
    NativeCount = sum(CheckEditGrid(CaseValue) for CaseValue in Cases)
    Verified = [CheckPadArchive(Directory, CaseValue, StrictSdk) for CaseValue in Cases]
    RequirePad(
        len({RowValue["archive_sha256"] for RowValue in Verified}) == 5,
        "Distinct discovery cases or the two baselines reuse an archive",
    )
    return {
        "schema": 1,
        "status": "verified_two_pad_discovery",
        "capture_source_revision": Revision,
        "report_sha256": ReportSha,
        "phase_archives": {"authoring_sha256": AuthorSha, "reopen_sha256": ReopenSha},
        "application_build": Report["application_build"],
        "process_ids": Processes,
        "stock_sha256": StockSha,
        "stock_controls": 4,
        "verified_native_observations": NativeCount,
        "strict_sdk_json_roundtrip": StrictSdk,
        "cases": Verified,
    }


# the command emits one deterministic result and keeps private inputs read only
def RunAudit() -> None:
    Parser = ArgumentParser(
        description="Verify a sealed licensed SOLIDWORKS two-pad discovery package offline."
    )
    Parser.add_argument("--run-directory", type=FilePath, required=True)
    Parser.add_argument("--repository", type=FilePath, default=KRepository)
    Parser.add_argument("--source-revision", required=True)
    Parser.add_argument("--report-sha256", required=True)
    Parser.add_argument("--authoring-sha256", required=True)
    Parser.add_argument("--reopen-sha256", required=True)
    Parser.add_argument("--strict-sdk", action="store_true")
    ArgsValue = Parser.parse_args()
    try:
        Result = AuditDiscovery(
            ArgsValue.run_directory,
            ArgsValue.repository,
            ArgsValue.source_revision,
            ArgsValue.report_sha256,
            ArgsValue.authoring_sha256,
            ArgsValue.reopen_sha256,
            ArgsValue.strict_sdk,
        )
    except (
        CalledProcessError,
        KeyError,
        OSError,
        RuntimeError,
        StopIteration,
        TypeError,
        ValueError,
    ) as Error:
        Parser.error(str(Error))
    Payload = DumpJson(Result, sort_keys=True, separators=(",", ":"), allow_nan=False)
    sys.stdout.buffer.write((Payload + "\n").encode("utf-8"))


if __name__ == "__main__":
    RunAudit()
