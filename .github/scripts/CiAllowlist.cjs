// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

const WorkflowRoot = ".github/workflows/";
const WorkflowPath = WorkflowRoot + "PullRequest.yml";
const QueuePath = WorkflowRoot + "MergeQueue.yml";
const QueueGate = "Merge queue acceptance";
const QueueJobs = [
  "Run the complete test suite",
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
const StaticChecks = {
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
  "SpdxHeaders.yml": {
    required: [
      "Verify changed file headers",
      "Reject unresolved SPDX header failure",
    ],
    optional: ["Remediate missing SPDX headers"],
    skip: [
      "Remediate missing SPDX headers",
      "Reject unresolved SPDX header failure",
    ],
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
const LabelChecks = {
  "PullRequestCI.yml": "Label CI changes",
  "PullRequestTests.yml": "Label test changes",
  "PullRequestDependencies.yml": "Label dependency changes",
  "PullRequestDocumentation.yml": "Label documentation changes",
  "PullRequestSize.yml": "Label changed LOC ratio",
  "PullRequestBreakingChange.yml": "Label declared breaking changes",
  "PullRequestDirection.yml": "Label dominant change direction",
};

function CiWorkflows(IsPull, IncludeAgg = false, Opened = false) {
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
    });
    return Workflows;
  }

  const Deferred = [...QueueJobs, "Analyze ${{ matrix.language }}"];
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
  Workflows.set("dynamic/github-code-quality/codeql", {
    event: "dynamic",
    required: [
      "Analyze (python)",
      "Analyze (java-kotlin)",
      "Analyze (javascript-typescript)",
    ],
  });
  for (const [File, Name] of Object.entries(LabelChecks))
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

module.exports = { CiWorkflows, WorkflowPath };
