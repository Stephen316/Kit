// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

function BuildReport(Checks, HeadSha) {
  const Report = Checks.filter(
    (Check) =>
      Check.name === "Greptile Review" &&
      Check.app?.id === 867647 &&
      Check.head_sha === HeadSha,
  ).sort((Left, Right) => Right.id - Left.id)[0];
  return {
    name: "Greptile Review",
    app: 867647,
    state:
      Report?.status !== "completed"
        ? "pending"
        : Report.conclusion === "success"
          ? "pass"
          : "fail",
    conclusion: Report?.conclusion || "missing or pending",
    url: Report?.html_url || Report?.details_url || "",
  };
}

module.exports = { BuildReport };
