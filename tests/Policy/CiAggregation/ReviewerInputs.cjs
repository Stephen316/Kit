// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

const {
  Reviewers,
} = require("../../../.agents/skills/standard-pr-practice/ReviewBot.json");

function BuildRequired(CaseMode, Verdict, Target = "0") {
  const Checks = [];
  const Statuses = [];
  for (const [Index, Reviewer] of Reviewers.entries()) {
    const Selected = Index === (Number(Target) || 0);
    if (Selected && CaseMode === "review-missing") continue;
    const Result = Selected && CaseMode === "review" ? Verdict : "success";
    const HeadSha = (
      Selected && CaseMode === "review-stale" ? "b" : "a"
    ).repeat(40);
    const Identity = Selected && CaseMode === "review-spoof" ? 1 : null;
    for (const [Position, Name] of Reviewer.Checks.entries()) {
      if (Selected && CaseMode === "review-partial" && Position > 0) continue;
      Checks.push({
        id: 950 + Checks.length,
        name: Name,
        app: { id: Identity ?? Reviewer.AppId },
        head_sha: HeadSha,
        check_suite: { id: 2 },
        status: Result === "pending" ? "in_progress" : "completed",
        conclusion: CaseMode.startsWith("queue") ? "failure" : Result,
      });
    }
    for (const [Position, Name] of Reviewer.Statuses.entries()) {
      if (
        Selected &&
        CaseMode === "review-partial" &&
        Position + Reviewer.Checks.length > 0
      )
        continue;
      Statuses.push({
        id: 950 + Statuses.length,
        context: Name,
        ref: HeadSha,
        creator: { id: Identity ?? Reviewer.UserId },
        state: CaseMode.startsWith("queue") ? "failure" : Result,
      });
    }
  }
  return { Checks, Statuses };
}

module.exports = { BuildRequired };
