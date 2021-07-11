import subprocess
import logging
from dataclasses import dataclass
from os import getenv, path
from typing import Any, List, Optional, Tuple

import pytest
import testinfra


CONTAINER_URL = "registry.opensuse.org/opensuse/tumbleweed:latest"
SELECTED_CONTAINER_RUNTIME: Optional[str] = None


@dataclass(frozen=True)
class Container:
    name: str
    url: str

    def launch_and_prepare_container(
        self, runner_binary: str
    ) -> Tuple[Any, str]:
        container_id = (
            subprocess.check_output(
                [runner_binary, "run", "-d", "-it", self.url, "/bin/sh"]
            )
            .decode()
            .strip()
        )
        subprocess.check_call(
            [
                runner_binary,
                "cp",
                path.abspath(
                    path.join(
                        path.dirname(__file__),
                        "..",
                        "..",
                        "kiwi",
                        "config",
                        "functions.sh",
                    )
                ),
                container_id + ":" + "/bin/functions.sh",
            ],
        )

        return (
            testinfra.get_host(f"{runner_binary}://{container_id}"),
            container_id,
        )

    @staticmethod
    def cleanup_container(runner_binary: str, container_id: str) -> None:
        subprocess.check_call([runner_binary, "rm", "-f", container_id])


TUMBLEWEED_CONTAINER = Container(
    name="Tumbleweed",
    url="registry.opensuse.org/opensuse/tumbleweed:latest",
)

CONTAINERS = [
    Container(
        name="Leap-15.3", url="registry.opensuse.org/opensuse/leap:15.3"
    ),
    Container(
        name="Leap-15.2", url="registry.opensuse.org/opensuse/leap:15.2"
    ),
    TUMBLEWEED_CONTAINER,
    Container(name="SLE-15-SP3", url="registry.suse.com/suse/sle15:15.3"),
    Container(name="SLE-15-SP2", url="registry.suse.com/suse/sle15:15.2"),
    Container(name="SLE-15-SP1", url="registry.suse.com/suse/sle15:15.1"),
    Container(
        name="SLE-12-SP5", url="registry.suse.com/suse/sles12sp5:latest"
    ),
    Container(name="centos:stream8", url="quay.io/centos/centos:stream8"),
]


@pytest.fixture(autouse=True, scope="session")
def _check_container_runtimes():
    """Fixture that checks whether the podman & docker runtimes work and
    selects one (either the only one that works or the one from the environment
    variable `CONTAINER_RUNTIME`).
    """
    localhost = testinfra.host.get_host("local://")

    runtimes = ["podman", "docker"]
    working_container_runtimes: List[str] = []

    for runtime in runtimes:
        if not localhost.exists(runtime):
            continue
        try:
            con, con_id = TUMBLEWEED_CONTAINER.launch_and_prepare_container(
                runtime
            )
            assert con.file("/etc/os-release").exists
            Container.cleanup_container(runtime, con_id)

            working_container_runtimes.append(runtime)
        except Exception as issue:
            logging.debug(issue)

    if len(working_container_runtimes) == 0:
        raise RuntimeError("No working container runtime found")
    elif len(working_container_runtimes) == 1:
        global SELECTED_CONTAINER_RUNTIME
        SELECTED_CONTAINER_RUNTIME = working_container_runtimes[0]
    else:
        assert len(working_container_runtimes) == 2

        runtime_choice = getenv("CONTAINER_RUNTIME", "podman").lower()
        if runtime_choice not in runtimes:
            raise ValueError(f"Invalid CONTAINER_RUNTIME {runtime_choice}")

        SELECTED_CONTAINER_RUNTIME = runtime_choice


def get_container_by_name(container_name: str = "Tumbleweed") -> Container:
    match = [c for c in CONTAINERS if c.name == container_name]
    assert len(match) == 1, "found {0} containers with the name {1}".format(
        len(match), container_name
    )

    return match[0]


def get_container_name(request) -> str:
    return getattr(request, "param", "Tumbleweed")


@pytest.fixture(scope="function")
def container_per_test(request, _check_container_runtimes):
    """Fixture that requests a new container for each function.

    By default the Tumbleweed container is used if no parameter is passed to
    this fixture.

    This fixture is pretty expensive, as it will launch and destroy a new
    container for **every** test function. Thus only use it for tests that
    perform extensive mutation, which you do not feel comfortable to undo
    quickly in the test.
    """
    assert SELECTED_CONTAINER_RUNTIME is not None
    container = get_container_by_name(get_container_name(request))
    con, container_id = container.launch_and_prepare_container(
        SELECTED_CONTAINER_RUNTIME
    )
    yield con
    Container.cleanup_container(SELECTED_CONTAINER_RUNTIME, container_id)


@pytest.fixture(scope="session")
def shared_container(request, _check_container_runtimes):
    """Fixture that requests a new container for the whole test session.

    By default the Tumbleweed container is used if no parameter is passed to
    this fixture.

    **Caution:** The container will be shared by all tests that request this
    fixture. You **must** ensure that you do not mutate the container in your
    test, as later tests could then fail due to your changes.
    """
    assert SELECTED_CONTAINER_RUNTIME is not None
    container = get_container_by_name(get_container_name(request))
    con, container_id = container.launch_and_prepare_container(
        SELECTED_CONTAINER_RUNTIME
    )
    yield con
    Container.cleanup_container(SELECTED_CONTAINER_RUNTIME, container_id)
