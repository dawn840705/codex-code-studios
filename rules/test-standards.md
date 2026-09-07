---
paths:
  - "tests/**"
---

# Test Standards

- Test naming: `test_[system]_[scenario]_[expected_result]` pattern
- Every test must have a clear arrange/act/assert structure
- Unit tests must not depend on external state (filesystem, network, database)
- Integration tests must clean up after themselves
- Performance tests must specify acceptable thresholds and fail if exceeded
- Test data must be defined in the test or in dedicated fixtures, never shared mutable state
- Mock external dependencies — tests should be fast and deterministic
- Every bug fix must have a regression test that would have caught the original bug

## Unity skinned-mesh coordinate checks

- When checking posed vertices, grounding, or bounds, establish the bake output's coordinate space and scale handling for the actual Unity version and renderer hierarchy. [Unity 6 BakeMesh documentation](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/SkinnedMeshRenderer.BakeMesh.html) defines `useScale: true` as compensating Transform scale and `false` as retaining the scaled size. Applying `TransformPoint` to already scaled bake vertices can apply scale twice. Do not infer this contract from the parameter name or prescribe one conversion for every mesh/import hierarchy.
- Use an independent expected world position from a known bone pose, not a second copy of the production bake/conversion formula. A synthetic single-bone fixture with local Y movement `.05` and Y scale `2` must independently establish world Y `.10`. In the verified Unity 6 fixture, `BakeMesh(false)` returns Y `.10`, then `TransformPoint` incorrectly produces `.20`; `BakeMesh(true)` returns `.05`, then `TransformPoint` produces `.10`. Check both renderer-owned scale and a scaled parent with a unit-scale renderer, alongside unit scale; build bindposes before moving the bone.
- If production and measurement share a faulty transform, their agreement is not passing evidence. Preserve the failed measurement as such and rerun against the independent pose assertion and actual product hierarchy. Culling bounds and a passing synthetic fixture alone do not prove visible feet are grounded throughout an animation.

## Examples

**Correct** (proper naming + Arrange/Act/Assert):

```gdscript
func test_health_system_take_damage_reduces_health() -> void:
    # Arrange
    var health := HealthComponent.new()
    health.max_health = 100
    health.current_health = 100

    # Act
    health.take_damage(25)

    # Assert
    assert_eq(health.current_health, 75)
```

**Incorrect**:

```gdscript
func test1() -> void:  # VIOLATION: no descriptive name
    var h := HealthComponent.new()
    h.take_damage(25)  # VIOLATION: no arrange step, no clear assert
    assert_true(h.current_health < 100)  # VIOLATION: imprecise assertion
```
