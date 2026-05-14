---
name: iris-off
description: Pause Iris conversation capture for this project. Sets is_on to false in .iris-config.yaml so the hooks no-op until you run $iris-on. Existing chat logs and last-response files are preserved; $iris-sync and $iris-relay still work for reading what's already on disk.
---

# $iris-off

1. Run this skill's `references/iris-toggle.sh` with `false` as the argument.
2. Confirm to the user that Iris is now off. The hooks will no-op until they run `$iris-on`. Existing files on disk are untouched.
