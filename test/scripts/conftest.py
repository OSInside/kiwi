from pytest_container import auto_container_parametrize, DerivedContainer


FUNCTIONS_COPY_CONTAINERFILE = """COPY kiwi/config/functions.sh /bin/functions.sh
"""


CONTAINERS = [
    DerivedContainer(base=url, containerfile=FUNCTIONS_COPY_CONTAINERFILE)
    for url in [
        "registry.opensuse.org/opensuse/leap:15.5",
        "registry.opensuse.org/opensuse/tumbleweed:latest",
        "registry.fedoraproject.org/fedora:latest"
    ]
]

(
    LEAP_15_5,
    TUMBLEWEED,
    FEDORA
) = CONTAINERS


CONTAINERS_WITH_ZYPPER = [
    LEAP_15_5,
    TUMBLEWEED
]


CONTAINERS_WITH_DNF = [
    FEDORA
]


def pytest_generate_tests(metafunc):
    auto_container_parametrize(metafunc)
