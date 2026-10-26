# Persistent native workloads

This owner adapter extends OMC to registered long-lived services. It uses the
host's native executable, systemd supervision and cgroup limits. It uses no
container engine. The bounded job broker and canary rebalancer retain their
existing contracts; they do not acquire arbitrary service migration authority.

`python3 scripts/native_service.py --help` exposes `verify`, `install`, `start`,
`stop`, `restart`, `status`, `enable` and `disable`. Effects require root, a
root-owned mode-600 registration and its exact SHA-256. Each workload has one
nonblocking lifecycle lock. A different registration cannot replace an active
unit. The workload owner performs application-specific data fencing, readiness,
cutover, rollback and public acceptance around this adapter.

The registration binds owner/UID, immutable release, architecture, executable,
working directory, a complete SHA-256 bundle manifest, existing secret-file
references, writable paths and CPU/RAM/process/restart budgets. Installation and
start reject changed or unmanifested files, symlinks, root workloads and unsupported
resource bounds. Secrets stay in host-owned environment files. systemd retains
restart and reboot supervision; `enable` is a separate explicit owner action.

`status` reads the actual main PID, executable identity, unit state, boot ID,
CPU accounting, RAM and task limits. `active` alone is not application health.
Observed cost is available to the existing OMC observation/feedback consumers;
this adapter does not claim automatic placement optimization or pooled memory.

The service configuration follows the upstream [systemd service contract](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)
and [execution contract](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html).
The installed host's `systemd-analyze verify` checks its supported directives.
Local regressions: `python3 -m unittest tests.test_native_service -v`.
Production acceptance belongs to the consuming workload's release receipt.
