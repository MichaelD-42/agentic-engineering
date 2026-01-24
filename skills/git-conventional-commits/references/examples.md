# Commit Examples

## Good Examples

### Feature (Minor)

```
feat(physics): add gravity to spirit shards
```

### Bug Fix (Patch)

```
fix(ui): resolve flickering health bar on resize
```

### Documentation (No Release)

```
docs: update readme with setup instructions
```

### Breaking Change (Major)

```
feat(api)!: switch to async/await for all db calls

BREAKING CHANGE: The database interface is now asynchronous. All callers must update to use await.
```

### Breaking Change (Alternative)

```
refactor!: drop support for Node 12
```

### With Scope and Body

```
fix(rendering): correct z-ordering for particles

Particles were previously rendering behind the background layer.
This change enforces a minimum depth of 10 for all particle emitters.
```

## Bad Examples

### Vague

```
update code
```

_Critique: No type, no scope, no description._

### Wrong Format

```
[Feature] Added new player controller
```

_Critique: Uses brackets instead of standard `feat:`, uses past tense._

### Mixing Types

```
fix bug and add feature
```

_Critique: Should be split into two commits._
