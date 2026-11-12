// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

const Expected = require("./ExpectedChecks.cjs");
const { BuildReviews } = require("./ReviewReports.cjs");
const { BuildRequired } = require("./ReviewerInputs.cjs");
const {
  Reviewers,
} = require("../../../.agents/skills/standard-pr-practice/ReviewBot.json");
const { BuildQueue } = require("./QueueInputs.cjs");

function BuildReports(CaseMode, Verdict, CheckName = "Scorecard") {
  const Checks = Expected.map((CheckName, Index) => ({
    id: Index + 1,
    name: CheckName,
    app: { id: 15368, slug: "github-actions" },
    check_suite: { id: 1 },
    status: "completed",
    conclusion: "success",
  }));
  const Reviews = BuildReviews(Verdict);
  const Required = BuildRequired(CaseMode, Verdict, CheckName);
  Checks.push(
    ...Reviews.Checks.map((Check) => ({ ...Check, id: Check.id + 100 })),
    ...Required.Checks,
  );
  const QueueData = BuildQueue(CaseMode, Verdict, CheckName);
  Checks.push(...QueueData.Checks);
  const Statuses = [...Reviews.Statuses, ...Required.Statuses];
  if (CaseMode === "check") Checks[0].conclusion = "failure";
  if (CaseMode === "status")
    Statuses.push({
      id: 900,
      context: Reviewers[0].Checks[0] || Reviewers[0].Statuses[0],
      creator: { id: 900, login: "build-service" },
      state: "failure",
    });
  if (CaseMode === "external")
    Checks.push({
      id: 901,
      name: Reviewers[0].Checks[0] || Reviewers[0].Statuses[0],
      app: { id: 901, slug: "external-ci" },
      check_suite: { id: 3 },
      status: "completed",
      conclusion: "neutral",
    });
  return {
    Checks: Checks.filter(
      (Check) =>
        CaseMode !== "queue-missing" || Check.name !== "Merge queue acceptance",
    ),
    Statuses,
    Runs: QueueData.Runs,
  };
}

module.exports = { BuildReports };
