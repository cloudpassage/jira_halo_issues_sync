import jlib
import pytest


class TestUnitConfigHelper:
    def test_unit_confighelper_bool_from_env_true_1(self, monkeypatch):
        monkeypatch.setenv("test_env", "True")
        result = jlib.ConfigHelper.bool_from_env("test_env")
        assert result is True
        return

    def test_unit_confighelper_bool_from_env_true_2(self, monkeypatch):
        monkeypatch.setenv("test_env", "true")
        result = jlib.ConfigHelper.bool_from_env("test_env")
        assert result is True
        return

    def test_unit_confighelper_bool_from_env_false_1(self, monkeypatch):
        monkeypatch.setenv("test_env", "False")
        result = jlib.ConfigHelper.bool_from_env("test_env")
        assert result is False
        return

    def test_unit_confighelper_bool_from_env_false_2(self, monkeypatch):
        monkeypatch.setenv("test_env", "trew")
        result = jlib.ConfigHelper.bool_from_env("test_env")
        assert result is False
        return

    def test_unit_confighelper_bool_from_env_default_false(self, monkeypatch):
        monkeypatch.delenv("test_env", raising=False)
        result = jlib.ConfigHelper.bool_from_env("test_env")
        assert result is False
        return

    def test_unit_confighelper_dict_from_env(self, monkeypatch):
        monkeypatch.setenv("test_env", "K:V;hithere:hello yourself")
        result = jlib.ConfigHelper.dict_from_env("test_env")
        desired = {"K": "V", "hithere": "hello yourself"}
        assert result == desired
        return

    def test_unit_confighelper_dict_from_env_empty_1(self, monkeypatch):
        monkeypatch.delenv("test_env", raising=False)
        result = jlib.ConfigHelper.dict_from_env("test_env")
        desired = {}
        assert result == desired
        return

    def test_unit_confighelper_dict_from_env_empty_2(self, monkeypatch):
        monkeypatch.setenv("test_env", "")
        result = jlib.ConfigHelper.dict_from_env("test_env")
        desired = {}
        assert result == desired
        return

    def test_unit_confighelper_int_from_env(self, monkeypatch):
        monkeypatch.setenv("test_env", "1")
        result = jlib.ConfigHelper.int_from_env("test_env")
        desired = 1
        assert result == desired
        return

    def test_unit_confighelper_int_from_env_validation_fail(self, monkeypatch):
        monkeypatch.setenv("test_env", "hello")
        canary = "alive"
        with pytest.raises(ValueError):
            result = jlib.ConfigHelper.int_from_env("test_env")
            canary = "dead"
        assert canary == "alive"
        return

    def test_unit_confighelper_int_from_env_empty(self, monkeypatch):
        monkeypatch.delenv("test_env", raising=False)
        result = jlib.ConfigHelper.int_from_env("test_env")
        assert result == 0
        return

    def test_unit_confighelper_list_from_env(self, monkeypatch):
        monkeypatch.setenv("test_env", "1,2,3,4;5")
        result = jlib.ConfigHelper.list_from_env("test_env")
        desired = ["1", "2", "3", "4;5"]
        assert result == desired
        return

    def test_unit_confighelper_list_from_env_empty(self, monkeypatch):
        monkeypatch.setenv("test_env", "")
        result = jlib.ConfigHelper.list_from_env("test_env")
        desired = [""]
        assert result == desired
        return

    def test_unit_confighelper_list_from_env_unset(self, monkeypatch):
        monkeypatch.delenv("test_env", raising=False)
        result = jlib.ConfigHelper.list_from_env("test_env")
        desired = []
        assert result == desired
        return

    def test_unit_confighelper_str_from_env(self, monkeypatch):
        monkeypatch.setenv("test_env", "1,2,3,4;5")
        result = jlib.ConfigHelper.str_from_env("test_env")
        desired = "1,2,3,4;5"
        assert result == desired
        return

    def test_unit_confighelper_str_from_env_empty(self, monkeypatch):
        monkeypatch.delenv("test_env", raising=False)
        result = jlib.ConfigHelper.str_from_env("test_env")
        desired = ""
        assert result == desired
        return
