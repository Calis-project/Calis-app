---
name: python-venv-management
description: Instructs the agent to always use the local .venv directory inside mediapipe_pose when running python commands, pip installs, or executing python scripts.
---

# Python VEnv Management Guidelines

## Instructions
- When executing Python commands or running scripts inside `mediapipe_pose/`, always reference the local Python executable at `./mediapipe_pose/.venv/Scripts/python.exe` (on Windows) or the corresponding virtual environment path.
- When installing packages, run the virtual environment pip: `./mediapipe_pose/.venv/Scripts/pip.exe install <package>`.

## Constraints
- Do NOT run global python or pip commands when working within the `mediapipe_pose` folder.
- Always verify that the virtual environment `.venv` is activated or explicitly referenced before running scripts.
