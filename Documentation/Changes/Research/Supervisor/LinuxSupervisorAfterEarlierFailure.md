# Run the Linux supervisor check after an independent failure

The Linux workflow runs the research supervisor suite after an earlier check fails if the locked environment was prepared successfully and the workflow is still running. The suite starts its own supervisor and controller processes. It uses the pinned Python 3.14 environment and the existing reserve witness selection. The earlier failing step still determines the job verdict.

At PR head `2bde5f07`, the P04 archive re-export failed before the supervisor suite and GitHub skipped the later step. Running the independent suite can capture the Linux reserve evidence while the archive failure still blocks the workflow. The revised workflow still needs hosted verification. [Prior Linux job](https://github.com/TryUniCAD/Kit/actions/runs/43791586077/job/133051099512) · [GitHub status checks in conditions](https://docs.github.com/en/actions/reference/workflows-and-actions/expressions#status-check-functions)
