const { Aggregate } = require("../../../.github/scripts/CiReports.cjs");
const { BuildReports } = require("./ReportInputs.cjs");
const Inputs = BuildReports(process.argv[2], process.argv[3], process.argv[4]);
const PullData = {
  number: 42,
  state: "open",
  head: { sha: "a".repeat(40), repo: { id: Inputs.Forked ? 2 : 1 } },
  base: { sha: "b".repeat(40) },
  changed_files: Inputs.Files.length,
};
const Context = {
  eventName: process.argv[2].startsWith("queue")
    ? "merge_group"
    : "pull_request_target",
  sha: "a".repeat(40),
  runId: 500,
  repo: { owner: "TryUniCAD", repo: "Kit" },
  payload: {
    action: "opened",
    pull_request: PullData,
    repository: { id: 1 },
    merge_group: { base_ref: "refs/heads/main", head_sha: "a".repeat(40) },
  },
};
const Responses = {
  listWorkflowRunsForRepo: Inputs.Runs,
  listForRef: Inputs.Checks,
  listCommitStatusesForRef: Inputs.Statuses,
  listFiles: Inputs.Files,
};
const Github = {
  graphql: async () => ({ repository: { mergeQueue: null } }),
  rest: {
    actions: { listWorkflowRunsForRepo: "listWorkflowRunsForRepo" },
    checks: { listForRef: "listForRef" },
    repos: {
      listCommitStatusesForRef: "listCommitStatusesForRef",
      compareCommits: async () => ({ data: { status: "ahead" } }),
    },
    pulls: {
      get: async () => ({ data: PullData }),
      listFiles: "listFiles",
    },
    git: {
      getCommit: async () => ({ data: { tree: { sha: "c".repeat(40) } } }),
    },
  },
  paginate: async (Method, Request) =>
    Method === "listCommitStatusesForRef"
      ? Responses[Method].filter(
          (Status) => !Status.ref || Status.ref === Request.ref,
        ).map((Status) => {
          const Report = { ...Status };
          delete Report.ref;
          return Report;
        })
      : Responses[Method],
};
let SummaryRows = [];
const Summary = {
  addHeading(Value) {
    process.stdout.write(`${Value}\n`);
    return this;
  },
  addRaw(Value) {
    process.stdout.write(Value);
    return this;
  },
  addTable(Value) {
    SummaryRows = Value;
    process.stdout.write(`${JSON.stringify(Value)}\n`);
    return this;
  },
  async write() {
    process.stdout.write("summary complete\n");
  },
};
Aggregate({
  github: Github,
  context: Context,
  core: {
    summary: Summary,
    info: (Value) => process.stdout.write(`${Value}\n`),
  },
})
  .then(() => {
    const Reported = new Set(SummaryRows.slice(1).map((Row) => Row[2]));
    const Missing = Inputs.Expected.filter(
      (Check) => !Reported.has(Check.html_url),
    );
    if (Missing.length)
      throw new Error(
        `CI jobs missing from the aggregate: ${Missing.map((Check) => Check.name).join(", ")}`,
      );
  })
  .catch((Failure) => {
    process.stderr.write(`${Failure.message}\n`);
    process.exitCode = 1;
  });
