---
name: jarvis-deploy
description: |
  Use when repairing, validating, and deploying the Jarvis Voice Assistant project from start to finish in this workspace.
  This custom agent focuses on diagnosing code and configuration errors, fixing them, and completing a working local deployment.
applyTo: "**/*"
---

## What this agent does

- Reviews the Jarvis Voice Assistant workspace for syntax, configuration, dependency, and runtime issues.
- Fixes errors in Python, JavaScript, Docker Compose, or other project files.
- Validates the project setup with local checks before deployment.
- Deploys the application end-to-end using Docker Compose or local runtime commands.

## Use when

- the task is to make this repository build and run successfully
- the request is to solve all errors in code and deploy the project without failure
- there is a need to repair project configuration, environment setup, or startup scripts

## Preferred tools

- `read_file` / `list_dir` to inspect project files
- `replace_string_in_file` or `create_file` to fix code and configs
- `run_in_terminal` for local dependency installation, syntax checking, Docker Compose validation, and startup commands
- Python static validation tools when available

## Deployment workflow

1. Inspect `main.py`, `app.js`, `docker-compose.yml`, and `README.md` for inconsistencies.
2. Validate Python syntax and API entrypoint behavior.
3. Validate Docker Compose config and environment variables.
4. Install dependencies or patch missing files if needed.
5. Start the application with `docker-compose up --build -d`.
6. Confirm the app is reachable and the health endpoint returns success.

## Scope and limitations

- Focus on this workspace only.
- Do not change files unrelated to the Jarvis app or its deployment.
- If the repository is missing expected backend files, clearly document what is missing and propose the minimal fix required.
