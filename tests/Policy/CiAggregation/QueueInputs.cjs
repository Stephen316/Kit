// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

function BuildQueue(CaseMode, Verdict, CheckName) {
  if (!CaseMode.startsWith("queue")) return { Checks: [], Runs: [] };
  return {
    Checks: [
      {
        id: 1000,
        name: CheckName,
        app: { id: 15368, slug: "github-actions" },
        check_suite: { id: 3 },
        status: Verdict === "pending" ? "in_progress" : "completed",
        conclusion: CaseMode === "queue-run" ? "success" : Verdict,
      },
    ],
    Runs: [
      {
        id: 400,
        workflow_id: 900,
        check_suite_id: 3,
        head_sha: "a".repeat(40),
        event: "merge_group",
        path: ".github/workflows/MergeQueue.yml",
        name: "Merge queue",
        status: Verdict === "pending" ? "in_progress" : "completed",
        conclusion: CaseMode === "queue-run" ? Verdict : "success",
      },
    ],
  };
}

module.exports = { BuildQueue };
