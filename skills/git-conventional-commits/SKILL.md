---
name: git-conventional-commits
description: Guide the user and agent to use conventional commits format for git messages. Use this skill when the user asks to "commit changes", "create a release", "explain commit format", or when performing any git commit action.
version: 1.0.0
---

# Conventional Commits & Semantic Release

## Overview

This skill ensures that all git commit messages follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. This structure enables automated versioning (Semantic Release) and creates a standardized project history.

## Core Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Key Rules

1.  **Type:** Must be one of the allowed types (see `references/commit-types.md`).
2.  **Scope:** Optional but recommended. Describes the part of the codebase affected (e.g., `physics`, `ui`, `deps`).
3.  **Description:** concise summary in imperative mood ("add" not "added").
4.  **Breaking Changes:** Must be indicated by a `!` after the type/scope or a `BREAKING CHANGE:` footer.

## When to Use This Skill

- Before running `git commit`.
- When the user asks to "save changes".
- When explaining why a version number bumped (Semantic Versioning).

## Reference Index

### 1. Allowed Types

> **See: `references/commit-types.md`**
>
> detailed list of types (`feat`, `fix`, `chore`, etc.) and their impact on version numbers.

### 2. Examples

> **See: `references/examples.md`**
>
> Good and bad examples of commit messages, including breaking changes.

## Workflow

1.  **Identify Change:** What did you do? (Fix a bug? Add a feature?)
2.  **Determine Impact:** Does it break backward compatibility?
3.  **Format Message:** Construct the header line `type(scope): description`.
4.  **Commit:** Use the formatted message.
