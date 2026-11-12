# AGENT.md — Rules for the Coding Agent

These rules are mandatory for every task in this repository.

## Language
- All code, comments, variable names, commit messages, file names, documentation, and reports must be in English.
- Never write Persian/Farsi text in any file, code, or commit.
- Never invent non-ASCII content (no emojis unless explicitly requested).

## Scope
- Only create or modify files explicitly listed in the current task.
- If you believe another file must be touched, stop and report it first. Do not modify it.
- Do not refactor, reformat, or "improve" files outside the current task scope.

## Before Writing Code
- For any task that writes or modifies Python code, first list a short PLAN in your report showing every file you will create or change.
- Do not proceed to code until the PLAN is listed in your report.

## After Every Task
- Update STATUS.md: current task, what was completed, what is next.
- If any error or mistake occurred, append a new numbered lesson to LESSONS.md using the format already present there.

## Code Style (Python)
- Python 3.10+.
- Variable, function, module names: snake_case.
- Class names: PascalCase.
- Constants: UPPER_SNAKE_CASE.
- 4 spaces indentation, UTF-8 encoding, LF line endings.
- No secrets, passwords, tokens, or connection strings with credentials in source files.
- Configuration comes from environment variables with sensible defaults.

## File Encoding
- All text files: UTF-8, LF line endings (except .bat/.ps1 which use CRLF as declared in .gitattributes).

## Forbidden
- Do not install dependencies unless the task explicitly says to.
- Do not run git commands (commit, push, checkout, etc.) unless the task explicitly says to.
- Do not add features, files, or "helpful" extras that were not requested.

## Reporting Format
Reply with this structure:
- FILES_CREATED: list of paths
- FILES_MODIFIED: list of paths
- PLAN: (only for code tasks)
- NOTES: any deviation, blocker, or observation
- LESSONS_ADDED: lesson IDs if any
