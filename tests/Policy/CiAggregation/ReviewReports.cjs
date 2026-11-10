// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

const {
  Comment,
} = require("../../../.agents/skills/standard-pr-practice/ReviewBot.json");
const KProviders = [
  [1082092, 191113872, "cubic-dev-ai"],
  [867647, 165735046, "greptile-apps"],
  [347564, 136622811, "coderabbitai"],
  [9999991, 9999992, Comment.split(" ")[0].slice(1)],
];

function BuildReviews(Verdict) {
  const Checks = [];
  const Statuses = [];
  for (const [AppId, UserId, Login] of KProviders) {
    Checks.push({
      id: Checks.length + 1,
      name: "Review report",
      app: { id: AppId, slug: Login },
      check_suite: { id: 2 },
      status: Verdict === "pending" ? "in_progress" : "completed",
      conclusion: Verdict === "pending" ? null : Verdict,
    });
    Statuses.push({
      id: Statuses.length + 1,
      context: `review-${Login}`,
      creator: { id: UserId, login: `${Login}[bot]` },
      state: Verdict === "neutral" ? "error" : Verdict,
    });
  }
  return { Checks, Statuses };
}

module.exports = { BuildReviews };
