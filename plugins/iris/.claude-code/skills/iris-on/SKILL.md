---
name: iris-on
description: Enable Iris conversation capture for this project. Sets is_on to true in .iris-config.yaml (creating the file if it doesn't exist) so the hooks fire normally on the next turn.
disable-model-invocation: true
allowed-tools: Bash
---

# Iris On

1. Run the toggle script:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/iris-toggle.sh" true
   ```
2. Confirm to the user that Iris is now on. The next `UserPromptSubmit` / `Stop` will be captured to disk.
