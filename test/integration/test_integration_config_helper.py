import jlib
import pytest


class TestIntegrationConfigHelper:
    def test_integration_confighelper_instantiate_narp(self, monkeypatch):
        monkeypatch.setenv("CRITICAL_ONLY", "True")
        monkeypatch.setenv("HALO_API_KEY", "abc123")
        monkeypatch.setenv("HALO_API_SECRET_KEY", "abc123")
        monkeypatch.setenv("JIRA_ISSUE_ID_FIELD", "abc123456")
        monkeypatch.setenv("JIRA_API_TOKEN", "abc123456")
        monkeypatch.setenv("JIRA_PROJECT_KEY", "ABC")
        monkeypatch.setenv("JIRA_ISSUE_TYPE", "bug")
        monkeypatch.setenv("ISSUE_CLOSE_TRANSITION", "closed")
        monkeypatch.setenv("ISSUE_STATUS_CLOSED", "closed")
        monkeypatch.delenv("ISSUE_REOPEN_TRANSITION", raising=False)
        monkeypatch.setenv("TIME_RANGE", "30")
        helper = jlib.ConfigHelper()
        assert helper
        req_check = helper.required_vars_are_set()
        assert req_check is False

    def test_integration_confighelper_instantiate(self, monkeypatch):
        monkeypatch.setenv("CRITICAL_ONLY", "True")
        monkeypatch.setenv("HALO_API_KEY", "abc123")
        monkeypatch.setenv("HALO_API_SECRET_KEY", "abc123")
        monkeypatch.setenv("JIRA_ISSUE_ID_FIELD", "abc123456")
        monkeypatch.setenv("JIRA_API_USER", "JOE@EXAMPLE.COM")
        monkeypatch.setenv("JIRA_API_URL", "abc123456")
        monkeypatch.setenv("JIRA_API_TOKEN", "abc123456")
        monkeypatch.setenv("JIRA_PROJECT_KEY", "ABC")
        monkeypatch.setenv("JIRA_ISSUE_TYPE", "bug")
        monkeypatch.setenv("ISSUE_CLOSE_TRANSITION", "closed")
        monkeypatch.setenv("ISSUE_STATUS_CLOSED", "closed")
        monkeypatch.setenv("ISSUE_REOPEN_TRANSITION", "reopened")
        monkeypatch.setenv("TIME_RANGE", "30")
        helper = jlib.ConfigHelper()
        assert helper
        assert helper.required_vars_are_set()
