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


@pytest.fixture(autouse=True)
def dont_use_proxy_setup_from_host(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """kiwi takes the proxy setup of the host into account for the
    package manager setup. The proxy setup of the host leaks into the
    test environment, which is undesirable as tests assert on the
    package manager environment and configuration. This fixture
    removes the proxy environment variables and points the proxy
    config files to non existing paths.

    This behavior can be turned off by adding the ``no_host_proxy_mock``
    marker.

    """
    if request.node.get_closest_marker("no_host_proxy_mock"):
        return

    for name in ("http_proxy", "https_proxy", "ftp_proxy", "no_proxy"):
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name.upper(), raising=False)
    monkeypatch.setattr("kiwi.defaults.HOST_SYSCONFIG_PROXY", "/nonexisting")
    monkeypatch.setattr("kiwi.defaults.HOST_DNF_CONFIG", "/nonexisting")
    monkeypatch.setattr(
        "kiwi.utils.proxy.HostProxy.get_apt_config", staticmethod(lambda: [])
    )
