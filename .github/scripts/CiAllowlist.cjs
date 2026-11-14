const WorkflowRoot = ".github/workflows/";
const WorkflowPath = WorkflowRoot + "PullRequest.yml";
const QueuePath = WorkflowRoot + "MergeQueue.yml";
const QueueGate = "Merge queue acceptance";
const QueueJobs = [
  "Run the complete test suite",
  "Test suite / Plan",
  "Test suite / Report",
  "Analyze actions",
  "Analyze python",
  "Bandit",
  "Semgrep",
  "pip-audit",
  "Safety",
  "Checkov",
  "detect-secrets",
  "Syft",
  "CycloneDX SBOM",
  "dlint",
  "Gitleaks",
  "Grype",
  "OSV-Scanner",
  "Scorecard",
  "Trivy",
  "TruffleHog",
];
const ShardJobs = /^Test suite \/ Shard \(\d+\)$/;
const KQualityPath = "dynamic/github-code-quality/codeql";
const KQualityRun = "Code Quality";
const KQualityJobs = /^Analyze \(.+\)$/;
const KQualitySources =
  /\.(?:cjs|cs|cts|go|java|js|jsx|kt|kts|mjs|mts|py|pyi|rb|ts|tsx)$/i;
const StaticChecks = {
  "FusionCompatibility.yml": {
    required: ["Fusion archive compatibility"],
  },
  "PythonQuality.yml": {
    required: ["Ruff", "Black", "Pyright", "Mypy"],
    preflight: "PR CI reuse (Python quality gate)",
  },
  "PythonSteering.yml": {
    required: ["Python steering"],
    preflight: "PR CI reuse (Python steering)",
  },
  "ExplicitImports.yml": {
    required: ["Reject Python wildcard imports"],
    preflight: "PR CI reuse (Explicit imports)",
  },
  "PathPolicies.yml": { required: ["Verify path policies"] },
  "SteeringSync.yml": {
    required: ["Verify repository skill"],
    preflight: "PR CI reuse (Steering synchronization)",
  },
  "WorkflowPins.yml": {
    required: ["Verify immutable workflow dependencies"],
    preflight: "PR CI reuse (Workflow pins)",
  },
  "RationaleComments.yml": {
    required: ["Verify rationale comments on changed sources"],
  },
  "WorkflowQuality.yml": {
    required: [
      "Zizmor",
      "actionlint",
      "Verify CI policy and pytest compatibility",
    ],
    preflight: "PR CI reuse (Workflow quality)",
  },
};
const TargetChecks = {
  "PullRequestCI.yml": "Label CI changes",
  "PullRequestTests.yml": "Label test changes",
  "PullRequestDependencies.yml": "Label dependency changes",
  "PullRequestDocumentation.yml": "Label documentation changes",
  "PullRequestSize.yml": "Label changed LOC ratio",
  "PullRequestBreakingChange.yml": "Label declared breaking changes",
  "PullRequestDirection.yml": "Label dominant change direction",
  "PullRequestDiffBreakdown.yml": "Publish diff breakdown",
};

function HasQualityCode(Files) {
  return Files.some((File) =>
    [File.filename, File.previous_filename].some(
      (Name) => typeof Name === "string" && KQualitySources.test(Name),
    ),
  );
}

function CiWorkflows(
  IsPull,
  IncludeAgg = false,
  Opened = false,
  Analyzed = false,
) {
  const Event = IsPull ? "pull_request" : "merge_group";
  const Workflows = new Map(
    Object.entries(StaticChecks).map(([File, Spec]) => [
      WorkflowRoot + File,
      { ...Spec, event: Event },
    ]),
  );
  if (!IsPull) {
    Workflows.set(QueuePath, {
      event: Event,
      required: [QueueGate, ...QueueJobs],
      matching: [ShardJobs],
    });
    return Workflows;
  }

  const Deferred = [
    ...QueueJobs,
    "Analyze ${{ matrix.language }}",
    "Test suite / Shard (${{ matrix.shard }})",
  ];
  Workflows.set(QueuePath, {
    event: Event,
    required: [QueueGate],
    optional: Deferred,
    skip: Deferred,
  });
  Workflows.set(WorkflowRoot + "ReleaseBuild.yml", {
    event: Event,
    required: ["Build and verify release artifacts"],
  });
  Workflows.set(KQualityPath, {
    event: "dynamic",
    required: [],
    matching: [KQualityJobs],
    expected: Analyzed ? KQualityRun : null,
  });
  for (const [File, Name] of Object.entries(TargetChecks))
    Workflows.set(WorkflowRoot + File, {
      event: "pull_request_target",
      required: [Name],
    });

  const FirstTime = ["Label first-time contributors"];
  Workflows.set(WorkflowRoot + "PullRequestFirstTimeContributor.yml", {
    event: "pull_request_target",
    required: Opened ? FirstTime : [],
    optional: FirstTime,
  });
  if (IncludeAgg)
    Workflows.set(WorkflowPath, {
      event: "pull_request_target",
      required: ["CI Agg"],
    });
  return Workflows;
}

module.exports = { CiWorkflows, HasQualityCode, WorkflowPath };
