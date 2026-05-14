---
name: iris-on
description: Enable Iris conversation capture for this project. Sets is_on to true in .iris-config.yaml (creating the file if it doesn't exist) so the hooks fire normally on the next turn.
---

# $iris-on

1. Run this skill's `references/iris-toggle.sh` with `true` as the argument.
2. Confirm to the user that Iris is now on. The next `UserPromptSubmit` / `Stop` will be captured to disk.
