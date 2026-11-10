// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

function BuildGreptile(CaseMode, Verdict) {
  if (CaseMode === "greptile-missing") return [];
  const Result = CaseMode === "greptile" ? Verdict : "success";
  return [
    {
      id: 950,
      name: "Greptile Review",
      app: { id: CaseMode === "greptile-spoof" ? 1 : 867647 },
      head_sha: (CaseMode === "greptile-stale" ? "b" : "a").repeat(40),
      check_suite: { id: 2 },
      status: Result === "pending" ? "in_progress" : "completed",
      conclusion: CaseMode.startsWith("queue") ? "failure" : Result,
    },
  ];
}

module.exports = { BuildGreptile };
