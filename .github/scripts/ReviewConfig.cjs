const Config = require("../../.agents/skills/standard-pr-practice/ReviewBot.json");

function ReadReviewers() {
  if (
    !Array.isArray(Config.Reviewers) ||
    !Config.Reviewers.length ||
    !Array.isArray(Config.ExcludedReports)
  )
    throw new Error("Invalid reviewer configuration");
  const Comments = new Set();
  const Accounts = new Set();
  for (const Reviewer of Config.Reviewers) {
    if (
      typeof Reviewer.Comment !== "string" ||
      !Reviewer.Comment.trim() ||
      Reviewer.Comment !== Reviewer.Comment.trim() ||
      /[\r\n]/.test(Reviewer.Comment) ||
      Comments.has(Reviewer.Comment) ||
      Accounts.has(Reviewer.UserId) ||
      !Array.isArray(Reviewer.Checks) ||
      !Array.isArray(Reviewer.Statuses) ||
      (!Reviewer.Checks.length && !Reviewer.Statuses.length)
    )
      throw new Error("Invalid or duplicate configured reviewer");
    for (const Reports of [Reviewer.Checks, Reviewer.Statuses])
      if (
        new Set(Reports).size !== Reports.length ||
        Reports.some(
          (Name) =>
            typeof Name !== "string" || !Name.trim() || Name !== Name.trim(),
        )
      )
        throw new Error("Invalid reviewer report names");
    Comments.add(Reviewer.Comment);
    Accounts.add(Reviewer.UserId);
  }
  for (const Provider of [...Config.Reviewers, ...Config.ExcludedReports])
    if (
      !Number.isSafeInteger(Provider.AppId) ||
      Provider.AppId <= 0 ||
      !Number.isSafeInteger(Provider.UserId) ||
      Provider.UserId <= 0
    )
      throw new Error("Invalid reviewer identity");
  return Config;
}

module.exports = { ReadReviewers };
