import pytest

from .conftest import (
    LEAP_15_2,
    LEAP_15_3,
    LEAP_15_4,
    SLE_12_SP5,
    SLE_15_SP1,
    SLE_15_SP2,
    SLE_15_SP3,
    SLE_15_SP4,
    TUMBLEWEED,
)


CONTAINER_IMAGES = [TUMBLEWEED]


def test_does_nothing_when_product_correct(auto_container_per_test):
    previous_contents = auto_container_per_test.connection.file(
        "/etc/products.d"
    ).listdir()
    auto_container_per_test.connection.run_expect(
        [0], ". /bin/functions.sh && suseSetupProduct"
    )
    assert auto_container_per_test.connection.file("/etc/products.d").listdir() == previous_contents


@pytest.mark.parametrize(
    "container_per_test,product_name",
    (
        (TUMBLEWEED, "openSUSE.prod"),
        (LEAP_15_2, "openSUSE.prod"),
        (LEAP_15_3, "Leap.prod"),
        (LEAP_15_4, "Leap.prod"),
        (SLE_15_SP4, "SLES.prod"),
        (SLE_15_SP3, "SLES.prod"),
        (SLE_15_SP2, "SLES.prod"),
        (SLE_15_SP1, "SLES.prod"),
        (SLE_12_SP5, "SLES.prod"),
    ),
    indirect=["container_per_test"],
)
def test_sets_baseproduct_from_etc_os_relesae(container_per_test, product_name):
    assert not container_per_test.connection.file("/etc/SuSE-brand").exists

    container_per_test.connection.run_expect([0], "rm /etc/products.d/baseproduct")
    container_per_test.connection.run_expect(
        [0], ". /bin/functions.sh && suseSetupProduct"
    )

    assert container_per_test.connection.file("/etc/products.d/baseproduct").exists
    assert container_per_test.connection.file("/etc/products.d/baseproduct").is_symlink
    assert container_per_test.connection.file("/etc/products.d/baseproduct").linked_to == "/etc/products.d/" + product_name


def test_sets_baseproduct_with_weird_os_release(auto_container_per_test):
    assert not auto_container_per_test.connection.file(
        "/etc/SuSE-brand"
    ).exists
    auto_container_per_test.connection.run_expect(
        [0], "rm /etc/products.d/baseproduct"
    )
    auto_container_per_test.connection.run_expect(
        [0],
        """cat <<EOF > /etc/os-release
NAME=openSUSE Tumbleweed
ID="opensuse-tumbleweed"
ID_LIKE="opensuse suse"
EOF
""",
    )

    auto_container_per_test.connection.run_expect(
        [0], ". /bin/functions.sh && suseSetupProduct"
    )
    assert auto_container_per_test.connection.file(
        "/etc/products.d/baseproduct"
    ).exists
    assert auto_container_per_test.connection.file(
        "/etc/products.d/baseproduct"
    ).is_symlink
    assert (
        auto_container_per_test.connection.file(
            "/etc/products.d/baseproduct"
        ).linked_to == "/etc/products.d/openSUSE.prod"
    )


def test_sets_baseproduct_from_prod_files(auto_container_per_test):
    auto_container_per_test.connection.run_expect(
        [0],
        """rm /etc/products.d/baseproduct
rm /etc/products.d/openSUSE.prod
touch /etc/products.d/10.prod
touch /etc/products.d/20.prod
""",
    )

    auto_container_per_test.connection.run_expect(
        [0], ". /bin/functions.sh && suseSetupProduct"
    )
    assert auto_container_per_test.connection.file(
        "/etc/products.d/baseproduct"
    ).exists
    assert auto_container_per_test.connection.file(
        "/etc/products.d/baseproduct"
    ).is_symlink
    assert (
        auto_container_per_test.connection.file(
            "/etc/products.d/baseproduct"
        ).linked_to == "/etc/products.d/20.prod"
    )
