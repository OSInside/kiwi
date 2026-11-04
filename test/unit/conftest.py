import inspect
import os
import sys
from typing import Any, Dict, Iterator, List, Tuple

import pytest

import kiwi.defaults

# The platform architecture as detected when the tests start, see
# restore_platform_name()
PLATFORM_MACHINE = kiwi.defaults.PLATFORM_MACHINE


@pytest.fixture(autouse=True)
def dont_use_kiwi_yml_from_host(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """kiwi will by default read runtime config files, which influence which
    utilities get chosen. The users config file leaks into the test environment,
    which is undesirable as certain tests assume that the default tool is XYZ
    and assert that. This fixture prevents the loading of the runtime config
    files by setting all paths to falsy values that hence are ignored.

    The runtime config is read once per process and kept in a module
    global, see RuntimeConfig. Each test starts with an empty runtime
    config instead, which is the result of reading no config files.
    Otherwise the first test of a process which creates a RuntimeConfig
    reads the config files of the host, and does so with the mocks of
    that test in place. A test which needs the config files to be read
    has to use RuntimeConfig(reread=True).

    This behavior can be turned off by adding the ``no_kiwi_yml_mock`` marker.

    """
    if request.node.get_closest_marker("no_kiwi_yml_mock"):
        return

    monkeypatch.setattr("kiwi.defaults.ETC_RUNTIME_CONFIG_DIR", "")
    monkeypatch.setattr("kiwi.defaults.ETC_RUNTIME_CONFIG_FILE", "")
    monkeypatch.setattr("kiwi.defaults.USR_RUNTIME_CONFIG_DIR", "")
    monkeypatch.setattr("kiwi.defaults.USR_RUNTIME_CONFIG_FILE", "")
    monkeypatch.setattr("kiwi.defaults.CUSTOM_RUNTIME_CONFIG_FILE", None)
    monkeypatch.setattr("kiwi.runtime_config.RUNTIME_CONFIG", {})


@pytest.fixture(autouse=True)
def restore_platform_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """Defaults.set_platform_name() sets the platform architecture in a
    module global of kiwi.defaults. Tests set it to test architecture
    specific code. Each test starts with the architecture detected when
    the tests started and the architecture a test sets is reset after
    it. Otherwise a test depends on the architecture set by the test
    which ran before it in the same process.

    """
    monkeypatch.setattr("kiwi.defaults.PLATFORM_MACHINE", PLATFORM_MACHINE)


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


@pytest.fixture(autouse=True)
def restore_process_state() -> Iterator[None]:
    """Tests set the command line arguments in sys.argv, and the code
    under test sets environment variables, e.g GRUB_DISABLE_OS_PROBER
    or TMPDIR. Both are restored after each test, a test must not
    depend on the arguments or environment of the test which ran
    before it in the same process.

    """
    argv = list(sys.argv)
    environment = dict(os.environ)
    yield
    sys.argv = argv
    if dict(os.environ) != environment:
        os.environ.clear()
        os.environ.update(environment)


def _get_kiwi_namespaces() -> List[Any]:
    """Provide the loaded kiwi modules along with the classes defined
    in them, which are the namespaces tests replace attributes of

    """
    namespaces: List[Any] = []
    for name, module in list(sys.modules.items()):
        if module is None or not (name == 'kiwi' or name.startswith('kiwi.')):
            continue
        namespaces.append(module)
        for value in list(vars(module).values()):
            if inspect.isclass(value) and value.__module__ == name:
                namespaces.append(value)
    return namespaces


@pytest.fixture(autouse=True)
def restore_kiwi_namespaces() -> Iterator[None]:
    """Many tests replace attributes of kiwi modules and classes in
    their setup method without restoring them, e.g

    .. code:: python

        kiwi.builder.disk.BootImage.new = Mock()

    Such a replacement stays in place for all tests which run after it
    in the same process. Which tests that are depends on the order and
    on the distribution of the tests to the processes of a parallel
    run. The attributes of the kiwi modules and of the classes defined
    in them are therefore restored after each test, including the
    teardown of its test class.

    """
    snapshot: List[Tuple[Any, Dict[str, Any]]] = [
        (namespace, dict(vars(namespace)))
        for namespace in _get_kiwi_namespaces()
    ]
    yield
    for namespace, attributes in snapshot:
        current = vars(namespace)
        for name in [name for name in current if name not in attributes]:
            delattr(namespace, name)
        for name, value in attributes.items():
            if current.get(name, _MISSING) is not value:
                setattr(namespace, name, value)


# marker for an attribute which does not exist
_MISSING = object()
