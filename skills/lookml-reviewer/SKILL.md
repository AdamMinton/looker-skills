---
name: lookml-reviewer
description: Review a LookML codebase or file to confirm its compliance with official best practices and style guidelines. Use this skill whenever the user asks to review, audit, check, or critique LookML code or a LookML project.
---

# LookML Reviewer Skill

This skill performs a rigorous code audit on LookML files, checking them against a bundled set of best practice references and style guidelines.

## Workflow Instructions

When invoked, execute the following steps precisely:

1. **Understand Scope**: Identify the Remote Repository URL (GitHub or GitLab) containing the LookML codebase the user wants to review.
   - **CRITICAL**: You MUST always ask the user for the branch name to review before proceeding, unless they explicitly provided it in their request.
2. **Retrieve and Analyze Codebase**: 
   - Execute the `fetch_lookml_repo_content` tool with the `<URL>`, `<TOKEN>`, and `<BRANCH>` to retrieve the full content of all `.lkml` files in the repository for that specific branch.
   - If the repo is public, pass an empty string for the token.
   - **NOTE**: The file content returned by the tool will have lines prefixed with line numbers in the format `N: content` (e.g., `1: view: orders {`). Use these numbers to identify line numbers for links.
   - Perform a comprehensive analysis of the returned repository content against Looker best practices.
   - *CRITICAL*: You must analyze the repository as a whole to provide a holistic review. You are responsible for the analysis; the tool only fetches the data.
3. **Compile Report**: Draft a highly verbose and comprehensive review report based on your analysis. The report must contain the following sections:
   - **Summary**: A high-level summary of the overall health of the codebase, naming the branch reviewed and key findings.
   - **Strengths**: A bulleted list highlighting code patterns that were done exceptionally well.
   - **Improvement Points**: A highly detailed breakdown of violations organized by file. For each file's points:
     - Describe the violation clearly. **Do NOT explicitly list or recite the full rules in the report.**
     - Suggest exactly how to fix it (providing code snippets).
     - **CRITICAL**: You MUST include the exact URL pointing to the specific file and line number(s) of the violation. Construct the full link carefully using the file path, repository URL, and the **specific branch** specified by the user. Do not guess the branch. Append the line suffix (e.g. `#L16` or `#L16-L19`) to the URL based on the line numbers discovered in the tool output.
     - **CRITICAL**: When quoting code or providing fix suggestions in the report, you MUST strip the line numbers and colon (e.g., convert `1: view: orders {` to `view: orders {`).
4. **Print Report**: Formulate the report and print it directly in the chat or console as your primary response. Do not save it to a file or an artifact.
