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

    def test_describe_asset_server(self):
        """Requires one server in the account."""
        asset_type = 'server'
        halo_obj = self.get_halo_object()
        halo_server_object = cloudpassage.Server(halo_obj.session)
        state = "active,missing,deactivated"
        query_result = halo_server_object.list_all(state=state)
        one_server_url = query_result[0]['url']
        result = halo_obj.describe(one_server_url)
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
        result = halo.describe(url)
        assert result is None

    def test_describe_issue(self):
        halo = self.get_halo_object()
        issues_obj = cloudpassage.Issue(halo.session, endpoint_version=3)
        target_issue = issues_obj.list_all()[0]
        pprint.pprint(target_issue)
        issue_url = target_issue["url"]
        result = halo.describe(issue_url)
        assert result is not None

    def test_describe_finding(self):
        halo = self.get_halo_object()
        issues_obj = cloudpassage.Issue(halo.session, endpoint_version=3)
        target_issue = issues_obj.list_all()[0]
        pprint.pprint(target_issue)
        finding_url = target_issue["last_finding_urls"][-1]
        result = halo.describe(finding_url)
        assert result is not None

    def test_describe_asset(self):
        halo = self.get_halo_object()
        issues_obj = cloudpassage.Issue(halo.session, endpoint_version=3)
        target_issue = issues_obj.list_all()[0]
        pprint.pprint(target_issue)
        asset_url = target_issue["asset_url"]
        result = halo.describe(asset_url)
        assert result is not None

    def test_deduplicate_issues(self):
        issues = [{"id": "12345"}, {"id": "123456"}, {"id": "12345"}]
        deduped = jlib.Halo.deduplicate_issues(issues)
        assert len(deduped) == 2
