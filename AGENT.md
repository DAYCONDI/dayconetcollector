# AGENT.md - Rules for the Coding Agent

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
- Any error, failed command, wrong assumption, or non-obvious correction - even one you recovered from within the same task - MUST be recorded as a new numbered lesson in LESSONS.md before the task is finished.
- "I recovered so no lesson is needed" is NOT an acceptable reason to skip recording.
- "No mistakes" in your final report is only valid if no command failed, no assumption was wrong, and no correction was made during the entire task.

## Conditionals in Prompts
- When a task says "if the previous report ...", "if the last task ...", "in the prior turn ...", or similar, evaluate the condition against the PREVIOUS agent report, not the report you are currently writing.
- If a conditional is TRUE, its required action MUST be performed even if the current task otherwise succeeded.
- Do not reinterpret "previous" as "current". If unclear, treat it as "previous".
- If you decide a conditional is FALSE, state in your report: "Conditional X evaluated FALSE because Y." If you cannot state a concrete reason, the conditional is TRUE.

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

## ASCII-only for meta files
- The files AGENT.md, LESSONS.md, and STATUS.md must contain ASCII characters only.
- No em-dashes, en-dashes, smart quotes, arrows, or any byte greater than 127.
- Use plain ASCII substitutes: "-" instead of em-dash, "->" instead of arrow, straight quotes instead of smart quotes.
- Verify by reading all bytes and asserting every byte is in 0x09, 0x0A, 0x0D, or 0x20-0x7E.
- This rule exists because PowerShell 5.1 defaults to CP1252 output, and non-ASCII text in these three files produces mojibake in reports and logs.
- Report bodies (the text the agent sends back) are also subject to ASCII-only. Use "-" for dashes and "->" for arrows in report text too, not just in files.


## Shell Commands (Windows 10 default shell)
- All shell commands must be compatible with Windows PowerShell 5.1, the default shell on Windows 10.
- Do NOT use Unix-only operators or tools: `&&`, `||`, `wc`, `grep`, `sed`, `awk`, `head`, `tail`, `find`, `xargs`, `rm -rf`, or backtick chaining.
- Use PowerShell-native equivalents instead:
  - Command chaining: `;` or `-and` / `-or`.
  - Line count: `(Get-Content -Path <file>).Count` or `Get-Content <file> | Measure-Object -Line`.
  - Text search: `Select-String -Pattern <regex> -Path <file>`.
  - Conditional on exit code: `if ($?) { ... }`.
- If unsure whether a command is PowerShell-5.1-compatible, use the simplest form that works in both PowerShell 5.1 and PowerShell 7+.

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
