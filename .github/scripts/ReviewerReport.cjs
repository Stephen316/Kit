// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

function BuildReport(Reviewer, Kind, Name, Checks, Statuses, HeadSha) {
  const Reports = Kind === "check" ? Checks : Statuses;
  const Report = Reports.filter((Item) =>
    Kind === "check"
      ? Item.name === Name &&
        Item.app?.id === Reviewer.AppId &&
        Item.head_sha === HeadSha
      : Item.context === Name &&
        Item.creator?.id === Reviewer.UserId &&
        Item.ref === HeadSha,
  ).sort((Left, Right) => Right.id - Left.id)[0];
  const Pending =
    !Report ||
    (Kind === "check"
      ? Report.status !== "completed"
      : Report.state === "pending");
  const Conclusion = Kind === "check" ? Report?.conclusion : Report?.state;
  return {
    name: Name,
    app: Reviewer.AppId,
    state: Pending ? "pending" : Conclusion === "success" ? "pass" : "fail",
    conclusion: Conclusion || "missing or pending",
    url: Report?.html_url || Report?.details_url || Report?.target_url || "",
  };
}

module.exports = { BuildReport };
