# Commit Types

This reference defines the allowed commit types and their mapping to Semantic Versioning (SemVer).

| Type       | Description                                                   | SemVer Impact                  |
| :--------- | :------------------------------------------------------------ | :----------------------------- |
| `feat`     | A new feature                                                 | **Minor** (`0.1.0` -> `0.2.0`) |
| `fix`      | A bug fix                                                     | **Patch** (`0.1.0` -> `0.1.1`) |
| `docs`     | Documentation only changes                                    | None (or Patch)                |
| `style`    | Formatting, missing semi-colons, etc (no code change)         | None                           |
| `refactor` | A code change that neither fixes a bug nor adds a feature     | None (or Patch)                |
| `perf`     | A code change that improves performance                       | Patch                          |
| `test`     | Adding missing tests or correcting existing tests             | None                           |
| `build`    | Changes that affect the build system or external dependencies | Patch                          |
| `ci`       | Changes to CI configuration files and scripts                 | None                           |
| `chore`    | Other changes that don't modify src or test files             | None                           |
| `revert`   | Reverts a previous commit                                     | Patch                          |

## breaking Changes

Regardless of the type, if a commit includes a **Breaking Change**:

- **Impact:** **Major** (`0.1.0` -> `1.0.0`)
- **Indication:**
  - `!` after type/scope: `feat(api)!: remove old endpoint`
  - Footer: `BREAKING CHANGE: The API no longer supports v1.`
