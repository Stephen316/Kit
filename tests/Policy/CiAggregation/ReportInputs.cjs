const { BuildExpected } = require("./ExpectedChecks.cjs");
const { BuildReviews } = require("./ReviewReports.cjs");

function BuildReports(CaseMode, Verdict, CheckName) {
  const IsQueue = CaseMode.startsWith("queue");
  const HeadSha = "a".repeat(40);
  const { Checks, Runs } = BuildExpected(IsQueue, HeadSha);
  const Expected = Checks.map(({ name, html_url }) => ({ name, html_url }));
  const Reviews = BuildReviews(Verdict);
  const Statuses = Reviews.Statuses;

  if (CaseMode === "check")
    Checks.find((Check) => Check.name === CheckName).conclusion = "failure";
  if (CaseMode === "status")
    Statuses.push({
      id: 900,
      context: "Ruff",
      creator: { id: 900, login: "build-service" },
      state: "failure",
    });

  const Ruff = Checks.find((Check) => Check.name === "Ruff");
  if (CaseMode === "external")
    Checks.push({
      ...Ruff,
      id: 901,
      app: { id: 901, slug: "external-ci" },
      conclusion: "failure",
    });
  if (CaseMode === "unlisted-job")
    Checks.push({
      ...Ruff,
      id: 902,
      name: "Unlisted job",
      conclusion: "failure",
    });
  if (CaseMode === "unlisted-run" || CaseMode === "spoof") {
    Runs.push({
      id: 903,
      check_suite_id: 903,
      head_sha: HeadSha,
      event: "pull_request",
      path: ".github/workflows/Unlisted.yml",
      name: "Unlisted workflow",
      status: "completed",
      conclusion: "failure",
    });
    Checks.push({
      ...Ruff,
      id: 903,
      check_suite: { id: 903 },
      conclusion: CaseMode === "spoof" ? "success" : "failure",
    });
  }

  if (CaseMode === "queue" || CaseMode === "queue-run") {
    const Run = Runs.find((Item) => Item.name === "Merge queue");
    const Target =
      CaseMode === "queue-run"
        ? Run
        : Checks.find(
            (Check) =>
              Check.check_suite.id === Run.check_suite_id &&
              Check.name === CheckName,
          );
    Target.status = Verdict === "pending" ? "in_progress" : "completed";
    Target.conclusion = Verdict;
  }

  return {
    Checks: [
      ...Checks.filter(
        (Check) =>
          !(
            CaseMode === "queue-missing" &&
            Check.name === "Merge queue acceptance"
          ) && !(CaseMode === "spoof" && Check === Ruff),
      ),
      ...Reviews.Checks,
    ],
    Statuses,
    Runs,
    Expected,
  };
}

module.exports = { BuildReports };
