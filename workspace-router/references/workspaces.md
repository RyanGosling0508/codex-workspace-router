# Host and workspace checklist

This public package contains no personal workspace inventory. Observe the current task's actual host, project roots, applicable AGENTS.md files, existing changes and acceptance criteria before delegating. A remembered path or sidebar entry is not authorization.

## Local and multi-root projects

- A desktop project can contain several repositories. Declare the specific read and write paths needed for this task; do not assume all roots are writable.
- Preserve user changes and protected inputs. For data-processing projects, distinguish original observations, derived candidates and accepted outputs. Do not modify a protected source just to make downstream validation pass.
- Follow the project's real acceptance criteria. File existence, a preview, a screenshot or a child's completion claim does not establish correctness. Identify what still requires human or device validation.
- Include test caches, build outputs, generated files and trackers in the write scope. A nominally read-only review must not silently run commands that write into the project.
- Use stable resource identifiers for shared render sessions, IDE projects, build directories, databases, device sessions and live services. Resource collisions matter across hosts. The main agent obeys the same reservations as children.
- Independent readers can coexist with one another. A reader cannot review a changing file as a stable snapshot. Wait for its writer or explicitly establish an immutable snapshot with authorized scope.

## SSH and remote hosts

A registered remote host or a broad home directory is not proof of a live session or an identified repository. Verify the connected execution host, actual repository/cwd, current local changes, instructions and available tools.

Keep work on the current execution host. Discover Python and model/delegation capabilities there. Local skill installation does not automatically install a skill, executable, or configuration remotely. If selectable subagents are unavailable, continue with the remote coordinator within authorization.

Protect live services and existing user changes. Isolate experimental sessions, caches and test data from real users/devices. Do not restart or deploy a service merely to verify a child's code. When the user explicitly authorizes such an operation, the coordinator verifies the exact host/service/scope and handles it under existing permissions.

The installer does not connect to SSH. Deploy this package to another host as a separate authorized setup operation, then verify discovery and tests on that host. Do not describe prepared scripts as a verified deployment.
