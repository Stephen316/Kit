// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

const { ReadReviewers } = require("../../../.github/scripts/ReviewConfig.cjs");
const { Reviewers, ExcludedReports } = ReadReviewers();
const KProviders = [...Reviewers, ...ExcludedReports];

function BuildReviews(Verdict) {
  const Checks = [];
  const Statuses = [];
  if (Verdict === "missing") return { Checks, Statuses };
  const StatusVerdict = ["pending", "success", "failure"].includes(Verdict)
    ? Verdict
    : "error";
  for (const Provider of KProviders) {
    for (const Name of ["Review report", ...(Provider.Checks ?? [])])
      Checks.push({
        id: 100 + Checks.length,
        name: Name,
        app: { id: Provider.AppId, slug: Provider.AppSlug },
        head_sha: "a".repeat(40),
        check_suite: { id: 2 },
        status: Verdict === "pending" ? "in_progress" : "completed",
        conclusion: Verdict === "pending" ? null : Verdict,
      });
    for (const Context of [
      `review-${Provider.AppSlug}`,
      ...(Provider.Statuses ?? []),
    ])
      Statuses.push({
        id: 100 + Statuses.length,
        context: Context,
        creator: { id: Provider.UserId, login: Provider.UserLogin },
        state: StatusVerdict,
      });
  }
  return { Checks, Statuses };
}

module.exports = { BuildReviews };
