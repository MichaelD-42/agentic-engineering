---
name: Code Review Assistant
description: This skill should be used when the user asks to "review this code", "code review for", "check this implementation", "is this code good", "review my changes", or "perform code review". Performs thorough code reviews focusing on quality, maintainability, test coverage, and adherence to project standards.
version: 0.2.0
---

# Code Review Assistant

Perform systematic code reviews to ensure quality, maintainability, and adherence to project standards.

## Purpose

This skill evaluates code quality across multiple dimensions: clarity, correctness, test coverage, performance, and alignment with project architecture. Use this skill at the "Verify" step of the development cycle and during phase acceptance.

## When to Use This Skill

Invoke when:

- Completing a feature or function
- Before committing code
- During acceptance phase
- After refactoring
- Reviewing pull requests
- Checking code quality

## Review Checklist

### 1. Code Quality

**Clarity and Readability**:

- ✅ Clear, descriptive function and variable names
- ✅ Functions are small and focused (< 20 lines ideally)
- ✅ No magic numbers or strings (use constants)
- ✅ Code is self-documenting
- ✅ Complex logic has explanatory comments

**Structure**:

- ✅ Proper separation of concerns
- ✅ SOLID principles followed
- ✅ No code duplication (DRY)
- ✅ Appropriate abstraction levels
- ✅ Consistent code style

**TypeScript**:

- ✅ Strict typing (no `any`)
- ✅ Proper use of interfaces and types
- ✅ Generic types where appropriate
- ✅ Non-null assertions used carefully
- ✅ Enums for fixed value sets

### 2. Testing

**Coverage**:

- ✅ Unit tests exist for new code
- ✅ Coverage meets targets (90%+ for core logic)
- ✅ Edge cases tested
- ✅ Error conditions tested
- ✅ Integration tests where needed

**Quality**:

- ✅ Tests are focused and isolated
- ✅ Tests use AAA pattern
- ✅ Descriptive test names
- ✅ No test interdependencies
- ✅ Tests are maintainable

### 3. Architecture & Performance

**Architecture**:

- ✅ Proper separation of concerns (model/view/controller)
- ✅ Loose coupling between components
- ✅ Events or dependency injection for communication
- ✅ State management follows established patterns
- ✅ Consistent with existing codebase

**Performance**:

- ✅ No unnecessary re-renders or recalculations
- ✅ Efficient algorithms (appropriate time complexity)
- ✅ Resource pooling where appropriate
- ✅ No memory leaks
- ✅ Proper cleanup and resource disposal

### 4. Documentation

**Code Documentation**:

- ✅ JSDoc for public APIs
- ✅ Complex logic explained
- ✅ @param and @returns documented
- ✅ Usage examples where helpful
- ✅ No outdated comments

**Commit Message**:

- ✅ Follows Conventional Commits
- ✅ Clear subject line
- ✅ Descriptive body
- ✅ References tests and coverage
- ✅ Lists breaking changes if any

## Review Process

### Step 1: Initial Scan

Read code to understand purpose and approach.

**Questions**:

- What problem does this solve?
- Is the solution appropriate?
- Is it consistent with project architecture?

### Step 2: Detailed Analysis

Examine code line by line for issues.

**Look for**:

- Code smells (long functions, deep nesting, duplication)
- Type safety issues
- Error handling gaps
- Performance concerns
- Security vulnerabilities

### Step 3: Test Review

Verify test quality and coverage.

**Check**:

- Tests exist and pass
- Coverage meets targets
- Edge cases covered
- Tests are clear and maintainable

### Step 4: Suggestions

Provide actionable feedback for improvement.

**Prioritize**:

- Critical: Must fix (bugs, security issues)
- Moderate: Should fix (complexity, maintainability)
- Minor: Nice to have (style, minor improvements)

## Output Format

### Review Summary

```
**Overall**: ✅ Good | ⚠️ Needs Improvement | ❌ Issues Found

**Strengths**:
✅ Clear function names
✅ Good test coverage (92%)
✅ Proper TypeScript typing

**Issues**:
❌ **Critical**: [Description]
   - Location: [File:Line]
   - Recommendation: [Fix]

⚠️ **Moderate**: [Description]
   - Location: [File:Line]
   - Recommendation: [Fix]

⚠️ **Minor**: [Description]
   - Location: [File:Line]
   - Recommendation: [Fix]

**Suggestions**:
- [Improvement idea 1]
- [Improvement idea 2]

**Action Items**:
1. [Required action]
2. [Required action]

**Approval**: ✅ Approved | ⚠️ Approve with changes | ❌ Changes required
```

## Common Issues

### Code Smells

**Long Function** (> 30 lines):

- Extract smaller functions
- Single Responsibility Principle

**Deep Nesting** (> 3 levels):

- Use early returns (guard clauses)
- Extract complex logic

**Code Duplication**:

- Extract shared logic
- Create utility functions

**Magic Numbers**:

```typescript
// Bad
if (user.status === 2) {
}

// Good
const STATUS_ACTIVE = 2;
if (user.status === STATUS_ACTIVE) {
}

// Better
enum UserStatus {
  PENDING = 0,
  INACTIVE = 1,
  ACTIVE = 2,
  SUSPENDED = 3,
}
if (user.status === UserStatus.ACTIVE) {
}
```

### TypeScript Issues

**Using `any`**:

```typescript
// Bad
function process(data: any) {}

// Good
function process(data: UserData) {}
```

**Missing Return Types**:

```typescript
// Bad
function getUser(id) {}

// Good
function getUser(id: string): User | null {}
```

### Testing Issues

**Missing Edge Cases**:

- Test negative values
- Test boundary values
- Test invalid inputs

**Unclear Test Names**:

```typescript
// Bad
it('test1', () => {});

// Good
it('returns null when position is out of bounds', () => {});
```

## Common Architecture Patterns

### Separation of Concerns

**Good**:

```typescript
// Service: Pure business logic
class OrderService {
  calculateTotal(items: OrderItem[]): number {
    // Pure calculation
  }
}

// Controller: HTTP handling
class OrderController {
  async handleRequest(req: Request): Promise<Response> {
    const total = this.orderService.calculateTotal(req.body.items);
    return Response.json({ total });
  }
}
```

**Bad**:

```typescript
// Mixed concerns
class OrderService {
  async calculateTotal(items: OrderItem[], res: Response): Promise<void> {
    // Calculate AND send response (tight coupling)
  }
}
```

### Event-Driven Communication

**Good**:

```typescript
// Emitter
this.eventBus.emit('order-created', { orderId, userId });

// Listener (in another service)
this.eventBus.on('order-created', this.sendConfirmationEmail, this);
```

**Bad**:

```typescript
// Direct coupling
this.emailService.sendConfirmationEmail(); // Called from order creation
```

### Resource Cleanup

**Good**:

```typescript
destroy(): void {
  this.eventBus.off();
  this.timers.forEach(t => clearTimeout(t));
  this.connections.forEach(c => c.close());
}
```

**Bad**:

```typescript
destroy(): void {
  // No cleanup - memory leak!
}
```

## Approval Criteria

### ✅ Approved

Code meets all quality standards:

- No critical issues
- Test coverage meets targets
- Follows project conventions
- Clear and maintainable
- Well-documented

### ⚠️ Approve with Changes

Code is functional but has minor issues:

- Some moderate issues to address
- Coverage slightly below target
- Minor refactoring beneficial
- Documentation incomplete

**Action**: Fix issues before next phase

### ❌ Changes Required

Code has significant issues:

- Critical bugs or security issues
- Missing test coverage
- Violates architecture
- Major refactoring needed
- Unreadable or unmaintainable

**Action**: Rework before proceeding

## Critical Reminders

- Review code, not the person
- Provide actionable, specific feedback
- Explain WHY something is an issue
- Suggest concrete improvements
- Acknowledge good practices
- Be constructive and respectful

Code review is not about perfection—it's about continuous improvement and maintaining quality standards while shipping working software.
