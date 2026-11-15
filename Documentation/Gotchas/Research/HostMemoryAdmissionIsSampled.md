# Host memory admission is sampled

## Expectation

A configured session memory limit can appear to prevent every allocation above that value.

## Actual behavior

The supervisor samples resident memory from `ps` during its existing supervision passes.
An allocation can exceed the threshold before the next observation and signal.
Host available memory does not establish a container's remaining memory quota.
The per-process `wait4` high-water mark also does not equal a simultaneous sum across the process group.
The macOS `vm_stat` page categories are separate counters without a disjointness guarantee in its manual.

## Workaround

Keep the sampled group peak and limit separate from the existing operating-system high-water value.
Keep configured headroom for allocations between samples.
Use conservative admission estimates and separate pools for materially different runner sizes.
Do not describe this mechanism as an operating-system hard allocation limit or cgroup containment.
For macOS admission, use free pages plus the larger of inactive or purgeable pages without assuming the counters are disjoint.

See [the resource change entry](../../Changes/Research/ResearchResourceHeadroom.md).
