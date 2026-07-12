"""Tests for profiles module."""

from mcp_cli.core.profiles import ProfileManager, BUILTIN_PROFILES


def test_builtin_profiles_contain_all_nine():
    """Test that 9 built-in profiles exist."""
    expected = [
        "backend", "frontend", "devops", "ai-llm", "security",
        "documentation", "data-engineering", "full-stack", "minimal",
    ]
    for name in expected:
        assert name in BUILTIN_PROFILES


def test_builtin_profiles_have_servers():
    """Test that each built-in profile has enabled servers."""
    for name, data in BUILTIN_PROFILES.items():
        assert len(data["enabled_servers"]) > 0, f"{name} has no enabled servers"


def test_profile_list_returns_all():
    """Test that list_profiles returns all built-ins."""
    mgr = ProfileManager()
    profiles = mgr.list_profiles()
    profile_ids = {p["id"] for p in profiles}
    for name in BUILTIN_PROFILES:
        assert name in profile_ids


def test_profile_info_exists():
    """Test that get_profile_info returns data for built-ins."""
    mgr = ProfileManager()
    for name in BUILTIN_PROFILES:
        info = mgr.get_profile_info(name)
        assert info is not None
        assert "enabled_servers" in info


def test_profile_info_nonexistent():
    """Test that get_profile_info returns None for unknown profiles."""
    mgr = ProfileManager()
    info = mgr.get_profile_info("nonexistent_profile_xyz")
    assert info is None


def test_auto_detect_no_workspace():
    """Test auto_detect returns None for non-existent workspace."""
    mgr = ProfileManager()
    result = mgr.auto_detect("/nonexistent/path/12345")
    assert result is None
