import cloudpassage
import jlib
import os
import pytest
import pprint
from datetime import datetime, timedelta


class TestIntegrationHalo:
    def get_halo_object(self):
        key = os.getenv("HALO_API_KEY")
        secret = os.getenv("HALO_API_SECRET_KEY")
        api_host = os.getenv("HALO_API_HOSTNAME")
        halo_obj = jlib.Halo(key, secret, api_host, 10)
        return halo_obj

    def get_iso_yesterday(self):
        dt_yest = datetime.now() - timedelta(1)
        return dt_yest.isoformat()

    def test_failed_auth(self):
        key = os.getenv("HALO_API_KEY")
        secret = "clearly_not_the_secret_you're_looking_for"
        api_host = os.getenv("HALO_API_HOSTNAME")
        with pytest.raises(cloudpassage.CloudPassageAuthentication):
            jlib.Halo(key, secret, api_host, 10)

    def test_get_unsupported_asset_type(self):
        halo = self.get_halo_object()
        result = halo.describe_asset("nonexistent", "12345")
        assert result == {}

    def test_describe_asset_server(self):
        """Requires one server in the account."""
        asset_type = 'server'
        halo_obj = self.get_halo_object()
        halo_server_object = cloudpassage.Server(halo_obj.session)
        state = "active,missing,deactivated"
        query_result = halo_server_object.list_all(state=state)
        one_server_id = query_result[0]["id"]
        result = halo_obj.describe_asset(asset_type, one_server_id)
        assert result != {}
        assert "id" in result

    def test_get_issues_touched_since_yesterday(self):
        halo = self.get_halo_object()
        issues = halo.get_issues_touched_since(self.get_iso_yesterday())
        assert issues

    def test_describe_issues_touched_since_yesterday_noncrit_included(self):
        halo = self.get_halo_object()
        issues_described = halo.describe_all_issues(self.get_iso_yesterday(),
                                                    critical_only=False)
        crits = [x for x in issues_described if x["critical"] is True]
        noncrits = [x for x in issues_described if x["critical"] is False]
        print("Crits: %s\tNon-crits: %s" % (len(crits), len(noncrits)))
        assert crits
        assert noncrits

    def test_describe_issues_touched_since_yesterday_critical_only(self):
        halo = self.get_halo_object()
        issues_described = halo.describe_all_issues(self.get_iso_yesterday(),
                                                    critical_only=True)
        total = len(issues_described)
        noncrits = [x for x in issues_described if x["critical"] is False]
        print("Crits: %s\tNon-crits: %s" % (total, len(noncrits)))
        assert not noncrits

    def test_describe_finding_bad(self):
        """Unrecognized URL."""
        url = "/v2/someotherthing"
        halo = self.get_halo_object()
        result = halo.describe_finding(url)
        assert result is None

    def test_describe_finding_sva(self):
        halo = self.get_halo_object()
        issues_obj = cloudpassage.Issue(halo.session)
        target_issue = issues_obj.list_all(status=["active", "resolved"],
                                           state=["active", "deactivated",
                                                  "missing", "retired"],
                                           issue_type="sva")[0]
        pprint.pprint(target_issue)
        finding_url = halo.get_issue_full(target_issue["id"])["findings"][-1]["finding"]  # NOQA
        result = halo.describe_finding(finding_url)
        assert result is not None

    def test_describe_finding_fim(self):
        halo = self.get_halo_object()
        issues_obj = cloudpassage.Issue(halo.session)
        target_issue = issues_obj.list_all(status=["active", "resolved"],
                                           state=["active", "deactivated",
                                                  "missing", "retired"],
                                           issue_type="fim")[0]
        pprint.pprint(target_issue)
        finding_url = halo.get_issue_full(target_issue["id"])["findings"][-1]["finding"]  # NOQA
        result = halo.describe_finding(finding_url)
        assert result is not None

    def test_describe_finding_csm(self):
        halo = self.get_halo_object()
        issues_obj = cloudpassage.Issue(halo.session)
        target_issue = issues_obj.list_all(status=["active", "resolved"],
                                           state=["active", "deactivated",
                                                  "missing", "retired"],
                                           issue_type="csm")[0]
        pprint.pprint(target_issue)
        finding_url = halo.get_issue_full(target_issue["id"])["findings"][-1]["finding"]  # NOQA
        result = halo.describe_finding(finding_url)
        assert result is not None

    def test_deduplicate_issues(self):
        issues = [{"id": "12345"}, {"id": "123456"}, {"id": "12345"}]
        deduped = jlib.Halo.deduplicate_issues(issues)
        assert len(deduped) == 2
