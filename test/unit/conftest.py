import pytest


@pytest.fixture(autouse=True)
def dont_use_kiwi_yml_from_host(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """kiwi will by default read runtime config files, which influence which
    utilities get chosen. The users config file leaks into the test environment,
    which is undesirable as certain tests assume that the default tool is XYZ
    and assert that. This fixture prevents the loading of the runtime config
    files by setting all paths to falsy values that hence are ignored.

    This behavior can be turned off by adding the ``no_kiwi_yml_mock`` marker.

    """
    if request.node.get_closest_marker("no_kiwi_yml_mock"):
        return

    monkeypatch.setattr("kiwi.defaults.ETC_RUNTIME_CONFIG_DIR", "")
    monkeypatch.setattr("kiwi.defaults.ETC_RUNTIME_CONFIG_FILE", "")
    monkeypatch.setattr("kiwi.defaults.USR_RUNTIME_CONFIG_DIR", "")
    monkeypatch.setattr("kiwi.defaults.USR_RUNTIME_CONFIG_FILE", "")
    monkeypatch.setattr("kiwi.defaults.CUSTOM_RUNTIME_CONFIG_FILE", None)
