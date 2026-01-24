# 🤖 Agentic Skills

> A curated collection of tested skills for AI coding assistants, designed to promote disciplined software development practices.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Overview

This repository contains a collection of **agentic skills** — structured instruction sets that guide AI coding assistants to follow disciplined software development practices. These skills are designed for tools like Claude Code and similar AI-powered development environments.

Each skill provides:
- **Clear trigger conditions** — When to activate the skill
- **Detailed instructions** — Step-by-step guidance for the AI agent
- **Quality gates** — Verification checkpoints to ensure proper execution
- **Anti-patterns** — Common mistakes to avoid

## 📚 Available Skills

| Skill | Description |
|-------|-------------|
| **[claudeception](skills/claudeception/SKILL.md)** | Continuous learning system that extracts reusable knowledge from work sessions and codifies it into new skills. *By [Ahmad Adi](https://github.com/OthmanAdi/Claudeception).* |
| **[code-review](skills/code-review/SKILL.md)** | Systematic code review focusing on quality, maintainability, test coverage, and adherence to project standards |
| **[dispatching-parallel-agents](skills/dispatching-parallel-agents/SKILL.md)** | Dispatch multiple agents to work on independent tasks in parallel. *By [Jesse Vincent](https://github.com/obra/superpowers).* |
| **[git-conventional-commits](skills/git-conventional-commits/SKILL.md)** | Enforce [Conventional Commits](https://www.conventionalcommits.org/) format for semantic versioning and clean git history |
| **[planning-with-files](skills/planning-with-files/SKILL.md)** | File-based planning with persistent task plans, findings, and progress tracking. *By [Ahmad Adi](https://github.com/OthmanAdi/planning-with-files).* |
| **[retrospective](skills/retrospective/SKILL.md)** | Structured retrospectives after development phases to capture learnings and drive continuous improvement |
| **[systematic-debugging](skills/systematic-debugging/SKILL.md)** | Root cause investigation before attempting fixes — no guessing, no random patches. *By [Jesse Vincent](https://github.com/obra/superpowers).* |
| **[test-driven-development](skills/test-driven-development/SKILL.md)** | Enforces strict TDD: write failing test first, minimal implementation, then refactor. *By [Jesse Vincent](https://github.com/obra/superpowers).* |
| **[verification-before-completion](skills/verification-before-completion/SKILL.md)** | Requires evidence before claiming success — no "should pass," only verified results. *By [Jesse Vincent](https://github.com/obra/superpowers).* |


## 🚀 Quick Start

### Installation

Copy individual skills or the entire `skills/` directory to your AI assistant's skills location:

```bash
# For Claude Code (user-wide)
cp -r skills/* ~/.claude/skills/

# For project-specific skills
cp -r skills/* .claude/skills/
```

### Using the AGENTS.md Template

The included `AGENTS.md` provides a template for configuring AI coding assistants with:
- Development standards and architecture principles
- Test-Driven Development workflow
- Git workflow with conventional commits
- Code quality requirements

Copy it to your project root and customize for your specific project:

```bash
cp AGENTS.md /path/to/your/project/
```

## 🎯 Philosophy

These skills embody several core principles:

### 1. **Evidence Over Assumptions**
Never claim something works without verification. Run the tests. Check the output. Then report.

### 2. **Root Cause Over Symptoms**
No random fixes. Investigate first, understand the problem, then implement a targeted solution.

### 3. **Test First, Always**
Write the failing test before the implementation. If you didn't see it fail, you don't know it tests the right thing.

### 4. **Continuous Learning**
Extract and codify knowledge from each session. Build a growing library of reusable skills.

### 5. **Parallel When Possible**
Independent tasks should run in parallel. Don't serialize what can be parallelized.

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---
