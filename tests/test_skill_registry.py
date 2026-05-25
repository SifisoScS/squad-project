"""
Self-tests for skills.registry.SkillRegistry (#6).
Tests registration, lookup, listing, describe, and chain() — no Claude API needed
for most tests (chain() is tested with a mock invoker).
"""
import pytest
from unittest.mock import patch
from skills.registry import Skill, SkillRegistry


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_skill(name: str, category: str = "test") -> Skill:
    return Skill(
        name=name,
        description=f"Test skill: {name}",
        category=category,
        system_prompt=f"You are a {name} expert.",
        tools=[],
    )


# ── Registration ──────────────────────────────────────────────────────────────

def test_register_and_get():
    skill = _make_skill("_test_reg_skill")
    SkillRegistry.register(skill)
    retrieved = SkillRegistry.get("_test_reg_skill")
    assert retrieved.name == "_test_reg_skill"
    assert retrieved.description == "Test skill: _test_reg_skill"


def test_register_overwrites_same_name():
    s1 = Skill(name="_dup", description="v1", category="test", system_prompt="v1")
    s2 = Skill(name="_dup", description="v2", category="test", system_prompt="v2")
    SkillRegistry.register(s1)
    SkillRegistry.register(s2)
    assert SkillRegistry.get("_dup").description == "v2"


def test_get_missing_raises_key_error():
    with pytest.raises(KeyError, match="not found"):
        SkillRegistry.get("__nonexistent_skill_xyz__")


def test_get_error_message_lists_available():
    SkillRegistry.register(_make_skill("_listed_skill"))
    with pytest.raises(KeyError) as exc_info:
        SkillRegistry.get("__nonexistent__")
    assert "_listed_skill" in str(exc_info.value)


# ── Listing ───────────────────────────────────────────────────────────────────

def test_list_skills_returns_all():
    import skills  # noqa — registers the full built-in catalog
    all_skills = SkillRegistry.list_skills()
    assert len(all_skills) >= 100  # we ship 100 skills


def test_list_skills_sorted_by_category_then_name():
    import skills  # noqa
    skills_list = SkillRegistry.list_skills()
    pairs = [(s.category, s.name) for s in skills_list]
    assert pairs == sorted(pairs)


def test_list_skills_filter_by_category():
    import skills  # noqa
    security = SkillRegistry.list_skills(category="security")
    assert len(security) > 0
    assert all(s.category == "security" for s in security)


def test_list_skills_unknown_category_returns_empty():
    result = SkillRegistry.list_skills(category="__no_such_category__")
    assert result == []


# ── Describe ─────────────────────────────────────────────────────────────────

def test_describe_returns_string():
    import skills  # noqa
    desc = SkillRegistry.describe()
    assert isinstance(desc, str)
    assert "## Available Skills" in desc


def test_describe_includes_skill_names():
    import skills  # noqa
    desc = SkillRegistry.describe()
    assert "`decompose`" in desc
    assert "`security_audit`" in desc


# ── Chain ─────────────────────────────────────────────────────────────────────

def test_chain_empty_raises():
    with pytest.raises(ValueError, match="at least one"):
        SkillRegistry.chain([], "some task")


def test_chain_calls_skills_in_order():
    """chain() must invoke each skill exactly once, in order."""
    call_order = []

    def mock_invoke(name, context, workspace=None):
        call_order.append(name)
        return f"output-of-{name}"

    with patch.object(SkillRegistry, "invoke", side_effect=mock_invoke):
        results = SkillRegistry.chain(["alpha", "beta", "gamma"], "task")

    assert call_order == ["alpha", "beta", "gamma"]
    assert list(results.keys()) == ["alpha", "beta", "gamma"]


def test_chain_pipes_output_to_next_skill():
    """Each skill's output must appear in the context passed to the next skill."""
    received_contexts = []

    def mock_invoke(name, context, workspace=None):
        received_contexts.append(context)
        return f"result-{name}"

    with patch.object(SkillRegistry, "invoke", side_effect=mock_invoke):
        SkillRegistry.chain(["s1", "s2"], "original task")

    # First skill receives the raw task
    assert received_contexts[0] == "original task"
    # Second skill receives the original task + s1's output
    assert "original task" in received_contexts[1]
    assert "result-s1" in received_contexts[1]


def test_chain_returns_all_outputs():
    def mock_invoke(name, context, workspace=None):
        return f"output:{name}"

    with patch.object(SkillRegistry, "invoke", side_effect=mock_invoke):
        results = SkillRegistry.chain(["x", "y"], "task")

    assert results["x"] == "output:x"
    assert results["y"] == "output:y"


def test_chain_single_skill_no_pipe():
    """A single-skill chain returns that skill's output without modification."""
    with patch.object(SkillRegistry, "invoke", return_value="solo output"):
        results = SkillRegistry.chain(["only"], "task")

    assert results == {"only": "solo output"}
