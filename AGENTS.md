# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

<!-- Describe your project here -->

## Development Commands

<!-- Add your project's commands here -->

## Architecture

<!-- Describe your project's architecture here -->

## Development Standards

### Architecture Principles

- Prefer composition over inheritance
- Use dependency injection for testability
- Implement proper error boundaries
- Follow SOLID principles

### Code Quality Requirements

- Write comprehensive error handling
- Include unit tests for new functionality (min 80% coverage)
- Use typesafety where applicable

### Security Practices

- Never log sensitive data (passwords, API keys, PII)
- Validate and sanitize all user inputs
- Use environment variables for secrets
- Implement proper authentication/authorization checks
- Review OWASP Top 10 vulnerabilities

## Development Workflow

**MANDATORY**: All development follows a rigorous Test-Driven Development (TDD) approach with two nested cycles.

**Mantra**: "Design -> Test -> Code -> Verify -> Reflect"

### Microcycle: Design - Test - Code - Verify

The microcycle applies to **every feature, function, or system** being built. Duration: Minutes to hours.

| Step           | Goal                     | Activities                                                                                        |
| -------------- | ------------------------ | ------------------------------------------------------------------------------------------------- |
| **1. Design**  | Understand what to build | Define requirements, identify inputs/outputs, determine edge cases, sketch interfaces             |
| **2. Test**    | Define expected behavior | Write failing unit tests (Red phase), write integration tests if needed, test edge cases          |
| **3. Code**    | Make tests pass          | Write minimal code to pass tests (Green phase), follow SOLID principles, refactor for clarity     |
| **4. Verify**  | Confirm correctness      | Run all tests, run linter, run type checker, check coverage, manual verification if needed        |

**TDD Red-Green-Refactor**:

1. **Red**: Tests fail (Step 2)
2. **Green**: Write minimal code to pass tests (Step 3)
3. **Refactor**: Improve code quality while keeping tests green

**After each microcycle**: Commit the completed work.

### Macrocycle: Requirements - Implement - Acceptance - Retrospective

The macrocycle applies to **larger features or phases**. Duration: Hours to days.

| Phase              | Goal                 | Activities                                                                                  |
| ------------------ | -------------------- | ------------------------------------------------------------------------------------------- |
| **1. Requirements**| Define scope         | Review requirements, break down into tasks, define acceptance criteria, identify risks      |
| **2. Implement**   | Build the feature    | Execute microcycles for each task, commit after each task, document as you go               |
| **3. Acceptance**  | Verify completion    | Run full test suite, verify all acceptance criteria, code review, check performance         |
| **4. Retrospective**| Reflect and improve | What went well? What to improve? Capture learnings, define action items                     |

**After each macrocycle**: Run the `retrospective` skill.

### Testing Strategy

**Test Pyramid**:

- **70% Unit Tests**: Fast, isolated, focused on logic
- **20% Integration Tests**: Component interactions
- **10% E2E Tests**: Full user flows

**Coverage Targets**:

- Core business logic: 90%+
- UI/rendering: 60%+
- Overall: 75%+

### Git Workflow

**Commit in meaningful small steps**:

- Each commit represents a single logical change
- Commit after completing each microcycle
- Use Conventional Commits format (see `git-conventional-commits` skill)

**Use short-lived feature branches**:

- Branch naming: `feat/`, `fix/`, `refactor/`, `test/`, `docs/`
- Merge back to main within hours/days
- Delete branches after merging
