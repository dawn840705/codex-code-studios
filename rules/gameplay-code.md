---
paths:
  - "src/gameplay/**"
---

# Gameplay Code Rules

- ALL gameplay values MUST come from external config/data files, NEVER hardcoded
- Use delta time for ALL time-dependent calculations (frame-rate independence)
- NO direct references to UI code — use events/signals for cross-system communication
- Every gameplay system must implement a clear interface
- State machines must have explicit transition tables with documented states
- Write unit tests for all gameplay logic — separate logic from presentation
- Document which design doc each feature implements in code comments
- No static singletons for game state — use dependency injection

## Runtime cleanup and ownership

- In Update/FixedUpdate/LateUpdate and equivalent hot paths, cache component and
  object lookups; avoid repeated `GetComponent*`, `Find*`, LINQ, and allocating
  physics queries. If dynamic discovery is necessary, use a bounded retry/event
  path and document measured cost, including when the target never appears.
- Do not derive a stable camera/weapon reference point every frame from animated
  renderer bounds or physics output. Establish a stable authored/cached anchor;
  when following live motion is intended, define that contract and test jitter.
- Give each mutable state one writer. Other systems submit inputs or read the
  result; check camera/aim/rotation ownership for feedback loops and overwrites.
- Remove task-only Editor tools when their job ends, after preserving any needed
  reproducible procedure. Keep supported reusable tools with an explicit owner.
- Zero static references do not prove dead code: inspect self-bootstrap,
  serialized assets/scenes, reflection, and Editor/menu entry points first.
- Before splitting a large controller, capture characterization tests. A partial
  file split can preserve behavior as a first step; it does not itself separate
  responsibilities. Then extract ownership incrementally and rerun the tests.

## Examples

**Correct** (data-driven):

```gdscript
var damage: float = config.get_value("combat", "base_damage", 10.0)
var speed: float = stats_resource.movement_speed * delta
```

**Incorrect** (hardcoded):

```gdscript
var damage: float = 25.0   # VIOLATION: hardcoded gameplay value
var speed: float = 5.0      # VIOLATION: not from config, not using delta
```
