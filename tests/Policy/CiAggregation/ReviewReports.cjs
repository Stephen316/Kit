// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

const {
  ReadReviewers,
} = require("../../../.github/scripts/ReviewConfig.cjs");
const { Reviewers, ExcludedReports } = ReadReviewers();
const KProviders = [...Reviewers, ...ExcludedReports];

function BuildReviews(Verdict) {
  const Checks = [];
  const Statuses = [];
  for (const { AppId, UserId, AppSlug, UserLogin } of KProviders) {
    Checks.push({
      id: Checks.length + 1,
      name: "Review report",
      app: { id: AppId, slug: AppSlug },
      check_suite: { id: 2 },
      status: Verdict === "pending" ? "in_progress" : "completed",
      conclusion: Verdict === "pending" ? null : Verdict,
    });
    Statuses.push({
      id: Statuses.length + 1,
      context: `review-${AppSlug}`,
      creator: { id: UserId, login: UserLogin },
      state: Verdict === "neutral" ? "error" : Verdict,
    });
  }
  return { Checks, Statuses };
}

module.exports = { BuildReviews };
