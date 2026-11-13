const { BuildExpected } = require("./ExpectedChecks.cjs");
const { BuildReviews } = require("./ReviewReports.cjs");

const KQualityPath = "dynamic/github-code-quality/codeql";
const KQualityAbsent = ["quality-fork", "quality-docs", "quality-missing"];

function IsQualityKept(CaseMode, CheckName) {
  if (KQualityAbsent.includes(CaseMode) || CaseMode === "quality-empty")
    return false;
  return CaseMode !== "quality-subset" || CheckName === "Analyze (python)";
}

function BuildReports(CaseMode, Verdict, CheckName) {
  const IsQueue = CaseMode.startsWith("queue");
  const HeadSha = "a".repeat(40);
  const Built = BuildExpected(IsQueue, HeadSha);
  const Quality = Built.Runs.find((Run) => Run.path === KQualityPath);
  const Removed = KQualityAbsent.includes(CaseMode);
  const Runs = Built.Runs.filter((Run) => !(Removed && Run === Quality));
  const Checks = Built.Checks.filter(
    (Check) =>
      Check.check_suite.id !== Quality?.check_suite_id ||
      IsQualityKept(CaseMode, Check.name),
  );
  const Expected = Checks.map(({ name, html_url }) => ({ name, html_url }));
  const Files =
    CaseMode === "quality-docs"
      ? [{ filename: "Documentation/Index.md", status: "modified" }]
      : [{ filename: "src/Example.py", status: "modified" }];
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
    Files,
    Forked: CaseMode === "quality-fork",
  };
}

module.exports = { BuildReports };
