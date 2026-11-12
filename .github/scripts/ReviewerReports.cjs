// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

const { ReadReviewers } = require("./ReviewConfig.cjs");
const { BuildReport } = require("./ReviewerReport.cjs");
const { Reviewers } = ReadReviewers();

function BuildRequired(Checks, Statuses, HeadSha) {
  return Reviewers.flatMap((Reviewer) => [
    ...Reviewer.Checks.map((Name) =>
      BuildReport(Reviewer, "check", Name, Checks, Statuses, HeadSha),
    ),
    ...Reviewer.Statuses.map((Name) =>
      BuildReport(Reviewer, "status", Name, Checks, Statuses, HeadSha),
    ),
  ]);
}

module.exports = { BuildRequired };
