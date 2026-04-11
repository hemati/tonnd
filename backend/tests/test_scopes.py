"""Tests for API scope definitions and enforcement."""

from src.auth.scopes import (
    ALL_SCOPES,
    SCOPE_EXPANSION,
    SCOPE_METRICS,
    expand_scopes,
    has_scope,
    metric_types_for_scopes,
)


class TestExpandScopes:
    def test_read_all_expands_to_all(self):
        expanded = expand_scopes(["read:all"])
        assert expanded == set(ALL_SCOPES)

    def test_single_scope_stays(self):
        expanded = expand_scopes(["read:vitals"])
        assert expanded == {"read:vitals"}

    def test_multiple_scopes(self):
        expanded = expand_scopes(["read:vitals", "read:sleep"])
        assert expanded == {"read:vitals", "read:sleep"}

    def test_read_all_plus_specific_deduplicates(self):
        expanded = expand_scopes(["read:all", "read:vitals"])
        assert expanded == set(ALL_SCOPES)

    def test_empty_scopes(self):
        expanded = expand_scopes([])
        assert expanded == set()


class TestHasScope:
    def test_has_direct_scope(self):
        assert has_scope(["read:vitals", "read:sleep"], "read:vitals") is True

    def test_missing_scope(self):
        assert has_scope(["read:vitals"], "read:sleep") is False

    def test_read_all_grants_everything(self):
        for scope in ALL_SCOPES:
            assert has_scope(["read:all"], scope) is True

    def test_empty_scopes_deny(self):
        assert has_scope([], "read:vitals") is False


class TestMetricTypesForScopes:
    def test_vitals_scope(self):
        types = metric_types_for_scopes(["read:vitals"])
        assert "heart_rate" in types
        assert "hrv" in types
        assert "spo2" in types
        assert "sleep" not in types

    def test_body_scope(self):
        types = metric_types_for_scopes(["read:body"])
        assert "weight" in types
        assert "body_composition" in types
        assert "heart_rate" not in types

    def test_read_all_includes_everything(self):
        types = metric_types_for_scopes(["read:all"])
        all_types = set()
        for metric_list in SCOPE_METRICS.values():
            all_types.update(metric_list)
        assert types == all_types

    def test_multiple_scopes_union(self):
        types = metric_types_for_scopes(["read:vitals", "read:sleep"])
        assert "heart_rate" in types
        assert "sleep" in types

    def test_recovery_scope_has_no_metric_types(self):
        types = metric_types_for_scopes(["read:recovery"])
        assert types == set()


class TestScopeConsistency:
    def test_all_scopes_have_metrics_entry(self):
        for scope in ALL_SCOPES:
            assert scope in SCOPE_METRICS

    def test_expansion_keys_exist(self):
        for key in SCOPE_EXPANSION:
            assert key == "read:all"
