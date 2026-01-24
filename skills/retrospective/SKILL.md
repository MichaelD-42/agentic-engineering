---
name: Retrospective Facilitator
description: This skill should be used when the user asks to "run retrospective", "phase retrospective", "retro for", "reflect on phase", or "retrospective analysis". Guides structured retrospectives after each development phase to capture learnings, identify improvements, and drive continuous improvement.
version: 0.1.0
---

# Retrospective Facilitator

Guide structured retrospectives to reflect on completed phases, capture learnings, and continuously improve the development process.

## Purpose

This skill facilitates retrospectives using a structured format to analyze what went well, what could improve, and what actions to take. Use this skill after completing each macrocycle phase (Req → Implement → Acceptance → **Retro**).

## When to Use This Skill

Invoke when:

- Completing a development phase
- After major milestone (Phase 1, 2, 3, etc.)
- When significant learning occurred
- After overcoming challenges
- Regularly (every phase completion)

## Retrospective Format

### Standard Template

**Phase Information**:

- Phase name and number
- Estimated vs actual time
- Key features implemented
- Team size (if applicable)

**Five Questions**:

1. What went well? ✅ (Celebrate successes)
2. What could be improved? 🔄 (Identify issues)
3. What did you learn? 📚 (Capture knowledge)
4. Any surprises? 😮 (Challenge assumptions)
5. Metrics review 📊 (Quantitative analysis)

**Analysis**:

- Pattern identification
- Root cause analysis
- Comparison to previous phases

**Action Items**:

- Concrete next steps
- Process improvements
- Technical improvements
- Learning goals

**Assessment**:

- Overall phase rating
- Confidence level for next phase
- Risk identification

## Facilitation Process

### Step 0: Gather Time Tracking Data (REQUIRED)

**BEFORE starting the retrospective**, gather ACTUAL duration for the phase from your time tracking system (e.g., `docs/time-tracking.md`, issue tracker, or time logging tool).

**Extract**:

- Start timestamp
- End timestamp
- Actual duration (in minutes, not hours!)

**CRITICAL**: Use ACTUAL duration from time tracking, NOT estimates. Time tracking provides ground truth.

### Step 1: Context Setting

Establish phase context and refresh memory.

**Questions to Ask**:

- Which phase is being retrospected?
- What were the main goals?
- What was the ACTUAL timeline? (from time tracking)
- What was accomplished?

### Step 2: What Went Well? ✅

Identify and celebrate successes.

**Prompts**:

- What are you proud of?
- What worked smoothly?
- Which practices were effective?
- What made you feel confident?
- Which tools/techniques helped?

**Examples**:

- "TDD approach caught 3 bugs before runtime"
- "BFS algorithm worked correctly on first try"
- "Test coverage exceeded expectations"
- "Performance was better than estimated"
- "Clear requirements prevented rework"

### Step 3: What Could Be Improved? 🔄

Identify challenges and inefficiencies.

**Prompts**:

- What took longer than expected?
- What was frustrating?
- What would you do differently?
- Where did you get stuck?
- What slowed you down?

**Examples**:

- "Integration tests took 2x longer than unit tests"
- "Spent 30 minutes debugging edge case"
- "Test setup was repetitive"
- "Unclear requirement needed clarification"
- "Third-party library documentation was hard to find"

### Step 4: What Did You Learn? 📚

Capture new knowledge and insights.

**Prompts**:

- What new skills did you develop?
- What surprised you about the technology?
- What patterns emerged?
- What would you teach others?
- What do you understand better now?

**Examples**:

- "TypeScript enums prevented bugs"
- "BFS is clearer when broken into small functions"
- "Test helpers significantly speed up test writing"
- "Early returns reduce complexity more than expected"
- "Visual feedback needs immediate response (< 100ms)"

### Step 5: Any Surprises? 😮

Identify unexpected outcomes and assumption challenges.

**Prompts**:

- What was unexpected?
- What assumptions were wrong?
- What worked better/worse than anticipated?
- What didn't match the plan?

**Examples**:

- "Performance was 2x better than target"
- "Color mixing edge cases weren't initially considered"
- "Framework's update cycle doesn't need optimization yet"
- "Tests found bug that manual testing missed"
- "Refactoring took less time than expected"

### Step 6: Metrics Review 📊

Analyze quantitative data.

**CRITICAL**: Use ACTUAL time from your time tracking system, NOT estimates!

**Key Metrics**:

- **Time**: Estimated vs actual (from time tracking!)
- **Test Coverage**: Percentage achieved
- **Bugs**: Found in testing vs manual
- **Performance**: Benchmarks vs targets
- **Code Quality**: Lines of code, complexity
- **Commits**: Number and quality

**Example Analysis**:

```
Estimated: 4-6 hours
Actual: 15 minutes ✅ (from time tracking)
Variance: 16-24x faster than estimate!

Test Coverage: 88% (target: 75%) ✅ Exceeded
Bugs in Testing: 3
Bugs in Manual: 0 ✅ All caught by tests

Performance: 2.3ms (target: <5ms) ✅✅ Exceeded

Commits: 5
Lines of Code: 347
```

**Time Tracking Reminder**:

- Always check your time tracking system FIRST
- Report actual duration in minutes
- Compare actual to initial estimates
- Update future estimates based on actual velocity

### Step 7: Pattern Identification

Identify recurring patterns across phases.

**Look For**:

- Repeated issues
- Consistent strengths
- Trends over time
- Predictable challenges

### Step 8: Action Items 🎯

Define concrete next steps.

**Good Action Items**:

- Specific and actionable
- Assigned responsibility (even if solo)
- Measurable outcome
- Reasonable scope

**Examples**:

- ✅ "Create test helper functions for grid setup"
- ✅ "Add edge case tests earlier in TDD cycle"
- ✅ "Research performance profiling tools for the framework"
- ❌ "Write better code" (too vague)
- ❌ "Be faster" (not actionable)

### Step 9: Overall Assessment

Provide holistic evaluation.

**Rating Scale**: 1-10

- 1-3: Significant issues, major rework needed
- 4-6: Acceptable, notable improvements needed
- 7-8: Good, minor improvements
- 9-10: Excellent, minimal improvements

**Assessment Components**:

- Quality of output
- Adherence to process
- Learning achieved
- Time efficiency
- Team satisfaction (if applicable)

## Output Format

```markdown
## Phase X Retrospective: [Phase Name]

**Date**: YYYY-MM-DD
**Duration**: X hours (estimated: Y hours)

### What Went Well ✅

- [Success 1]
- [Success 2]
- [Success 3]

### What Could Be Improved 🔄

- [Challenge 1]
  - **Action**: [How to address]
- [Challenge 2]
  - **Action**: [How to address]

### Learnings 📚

- [Learning 1]
- [Learning 2]
- [Learning 3]

### Surprises 😮

- [Surprise 1]
- [Surprise 2]

### Action Items for Next Phase 🎯

1. [Action item 1]
2. [Action item 2]
3. [Action item 3]

### Metrics 📊

- **Estimated Time**: X hours
- **Actual Time**: X hours
- **Test Coverage**: X% (target: Y%)
- **Tests Written**: X (unit: Y, integration: Z)
- **Bugs Found in Testing**: X
- **Bugs Found in Manual Testing**: X
- **Commits**: X
- **Lines of Code**: X

### Overall Assessment

**Rating**: X/10

[Brief summary of phase success, key achievements, areas for improvement]

### Next Phase Preview

**Phase X+1**: [Name]

- [Brief description]
- Estimated: X hours
```

## Retrospective Patterns

### Common Success Patterns

**TDD Success**:

- Tests caught bugs early
- Refactoring was safe
- Code quality high
- Confidence in changes

**Clear Requirements**:

- No rework needed
- Smooth implementation
- Met acceptance criteria
- On time/budget

**Good Tools**:

- Increased productivity
- Reduced friction
- Better code quality
- Faster feedback

### Common Challenge Patterns

**Unclear Requirements**:

- Rework necessary
- Time overruns
- Scope creep
- Missed acceptance criteria

**Insufficient Testing**:

- Bugs found late
- Refactoring risky
- Low confidence
- Manual testing burden

**Tool Friction**:

- Decreased productivity
- Workarounds needed
- Frustration
- Time waste

### Continuous Improvement

Track action items across retrospectives:

**Phase 4 Action**: Create test helpers
**Phase 5 Check**: Were test helpers created? Did they help?

**Phase 3 Action**: Add edge case tests earlier
**Phase 4 Check**: Were edge cases tested earlier? Impact?

## Retrospective Anti-Patterns

**Avoid**:

- ❌ Blaming individuals
- ❌ Focusing only on negatives
- ❌ Vague action items
- ❌ Ignoring metrics
- ❌ Not tracking previous actions
- ❌ Skipping retrospectives
- ❌ Making retrospectives too long
- ❌ Not implementing action items

**Do**:

- ✅ Focus on process, not people
- ✅ Celebrate successes
- ✅ Create specific actions
- ✅ Use data to inform decisions
- ✅ Track improvement over time
- ✅ Do retros consistently
- ✅ Keep retros focused (30-45 min)
- ✅ Follow through on actions

## Critical Reminders

- Retrospectives are REQUIRED after each phase
- Be honest about challenges and failures
- Celebrate successes, even small ones
- Create actionable, specific next steps
- Track and review previous action items
- Use metrics to inform decisions
- Focus on continuous improvement
- Document learnings for future reference

Retrospectives are not about assigning blame—they're about learning, improving, and building better software through reflection and adaptation.
