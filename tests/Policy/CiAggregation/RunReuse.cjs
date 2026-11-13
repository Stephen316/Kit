const Fs = require("node:fs");
const Path = require("node:path");
const Crypto = require("node:crypto");
const Process = require("node:child_process");
const { SetReuse } = require("../../../.github/scripts/CiReports.cjs");
const { BuildExpected } = require("./ExpectedChecks.cjs");

const CaseMode = process.argv[2];
const BaseSha = "b".repeat(40);
const HeadSha = "a".repeat(40);
const CandidateSha = "c".repeat(40);
const MergeSha = "d".repeat(40);
const OtherSha = "e".repeat(40);
const TreeSha = "f".repeat(40);
const GroupBase = CaseMode === "base" ? "9".repeat(40) : BaseSha;
const QueueBranch = CaseMode === "branch" ? "release" : "main";
const QueuedNumber = ["unnamed", "ancestor"].includes(CaseMode) ? 41 : 42;
const AggregateRun = {
  id: 77,
  check_suite_id: 77,
  run_attempt: 1,
  head_sha: HeadSha,
  event: "pull_request_target",
  path: ".github/workflows/PullRequest.yml",
  name: "Pull Request",
  status: "completed",
  conclusion: "success",
  html_url: "https://github.example/runs/77",
};
const { Runs, Checks } = BuildExpected(false, HeadSha);
Runs.push(AggregateRun);
Checks.push({
  id: Checks.length + 1,
  name: "CI Agg",
  head_sha: HeadSha,
  app: { id: 15368, slug: "github-actions" },
  check_suite: { id: AggregateRun.check_suite_id },
  status: "completed",
  conclusion: "success",
  html_url: "https://github.example/jobs/aggregate",
});

const WorkPath = Fs.mkdtempSync(Path.join(process.env.RUNNER_TEMP, "Reuse-"));
Fs.writeFileSync(
  Path.join(WorkPath, "Evidence.json"),
  JSON.stringify({
    format: "pr-head-tree-v1",
    workflow_event: "pull_request_target",
    repository_id: 1,
    head_repository_id: 1,
    pull_number: 42,
    head_sha: HeadSha,
    base_sha: BaseSha,
    head_tree_sha: TreeSha,
    base_is_ancestor: true,
    report_merge_sha: MergeSha,
    run_id: AggregateRun.id,
    run_attempt: AggregateRun.run_attempt,
  }),
);
Process.execFileSync("zip", ["-q", "-X", "Evidence.zip", "Evidence.json"], {
  cwd: WorkPath,
});
const ArchiveBytes = Fs.readFileSync(Path.join(WorkPath, "Evidence.zip"));
const Artifact = {
  id: 9,
  name: `PrCiEvidence-${AggregateRun.run_attempt}`,
  expired: false,
  size_in_bytes: ArchiveBytes.length,
  digest: `sha256:${Crypto.createHash("sha256").update(ArchiveBytes).digest("hex")}`,
};
const Commits = {
  [CandidateSha]: {
    tree: { sha: CaseMode === "tree" ? "8".repeat(40) : TreeSha },
    parents: [{ sha: GroupBase }],
  },
  [HeadSha]: { tree: { sha: TreeSha }, parents: [{ sha: BaseSha }] },
  [MergeSha]: {
    tree: { sha: TreeSha },
    parents: [{ sha: BaseSha }, { sha: HeadSha }],
  },
};
const PullHeads = { 42: HeadSha, 43: OtherSha };

const Context = {
  eventName: "merge_group",
  runId: 500,
  repo: { owner: "TryUniCAD", repo: "Kit" },
  payload: {
    repository: { id: 1 },
    merge_group: {
      base_ref: "refs/heads/main",
      base_sha: GroupBase,
      head_sha: CandidateSha,
      head_ref: `refs/heads/gh-readonly-queue/${QueueBranch}/pr-${QueuedNumber}-${GroupBase}`,
    },
  },
};
const Github = {
  graphql: async () => ({
    repository: {
      mergeQueue: {
        entries: {
          pageInfo: { hasNextPage: false, endCursor: null },
          nodes: Object.entries(PullHeads).map(([Key, Sha]) => ({
            pullRequest: {
              number: Number(Key),
              headRefOid: Sha,
              baseRefName: "main",
              state: "OPEN",
            },
          })),
        },
      },
    },
  }),
  rest: {
    actions: {
      listWorkflowRunsForRepo: "listWorkflowRunsForRepo",
      listWorkflowRunArtifacts: "listWorkflowRunArtifacts",
      downloadArtifact: async () => ({ data: ArchiveBytes }),
    },
    checks: { listForRef: "listForRef" },
    repos: {
      compareCommits: async ({ base, head }) => ({
        data: {
          status:
            (base === GroupBase && head === HeadSha) ||
            (CaseMode === "ancestor" &&
              base === HeadSha &&
              head === CandidateSha)
              ? "ahead"
              : "diverged",
        },
      }),
    },
    pulls: {
      get: async ({ pull_number }) => ({
        data: {
          state: "open",
          head: { sha: PullHeads[pull_number], repo: { id: 1 } },
        },
      }),
    },
    git: {
      getCommit: async ({ commit_sha }) => ({ data: Commits[commit_sha] }),
    },
  },
  paginate: async (Method, Request) => {
    if (Method === "listWorkflowRunsForRepo")
      return Runs.filter(
        (Run) =>
          Run.head_sha === Request.head_sha &&
          (!Request.event || Run.event === Request.event),
      );
    if (Method === "listForRef")
      return Checks.filter((Check) => Check.head_sha === Request.ref);
    if (Method === "listWorkflowRunArtifacts")
      return Request.run_id === AggregateRun.id ? [Artifact] : [];
    throw new Error(`Unexpected paginated request: ${Method}`);
  },
};
const Outputs = {};
const Summary = {
  addHeading(Value) {
    process.stdout.write(`${Value}\n`);
    return this;
  },
  addRaw(Value) {
    process.stdout.write(Value);
    return this;
  },
  async write() {
    process.stdout.write("summary complete\n");
  },
};
SetReuse({
  github: Github,
  context: Context,
  core: {
    summary: Summary,
    info: (Value) => process.stdout.write(`${Value}\n`),
    setOutput: (Name, Value) => {
      Outputs[Name] = Value;
    },
  },
})
  .then(() => process.stdout.write(`reuse=${Outputs.reuse}\n`))
  .catch((Failure) => {
    process.stderr.write(`${Failure.message}\n`);
    process.exitCode = 1;
  });
