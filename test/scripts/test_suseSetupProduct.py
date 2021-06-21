import pytest


def test_does_nothing_when_product_correct(shared_container):
    previous_contents = shared_container.file("/etc/products.d").listdir()
    shared_container.run_expect([0], ". /bin/functions.sh && suseSetupProduct")
    assert (
        shared_container.file("/etc/products.d").listdir() == previous_contents
    )


@pytest.mark.parametrize(
    "shared_container,product_name",
    (
        ("Tumbleweed", "openSUSE.prod"),
        ("Leap-15.2", "openSUSE.prod"),
        ("Leap-15.3", "Leap.prod"),
        ("SLE-15-SP3", "SLES.prod"),
        ("SLE-15-SP2", "SLES.prod"),
        ("SLE-15-SP1", "SLES.prod"),
        ("SLE-12-SP5", "SLES.prod"),
    ),
    indirect=["shared_container"],
)
def test_sets_baseproduct_from_etc_os_relesae(shared_container, product_name):
    assert not shared_container.file("/etc/SuSE-brand").exists

    shared_container.run_expect([0], "rm /etc/products.d/baseproduct")
    shared_container.run_expect([0], ". /bin/functions.sh && suseSetupProduct")

    assert shared_container.file("/etc/products.d/baseproduct").exists
    assert shared_container.file("/etc/products.d/baseproduct").is_symlink
    assert (
        shared_container.file(
            "/etc/products.d/baseproduct"
        ).linked_to == "/etc/products.d/" + product_name
    )


def test_sets_baseproduct_with_weird_os_release(container_per_test):
    assert not container_per_test.file("/etc/SuSE-brand").exists
    container_per_test.run_expect([0], "rm /etc/products.d/baseproduct")
    container_per_test.run_expect(
        [0],
        """cat <<EOF > /etc/os-release
NAME=openSUSE Tumbleweed
ID="opensuse-tumbleweed"
ID_LIKE="opensuse suse"
EOF
""",
    )

    container_per_test.run_expect(
        [0], ". /bin/functions.sh && suseSetupProduct"
    )
    assert container_per_test.file("/etc/products.d/baseproduct").exists
    assert container_per_test.file("/etc/products.d/baseproduct").is_symlink
    assert (
        container_per_test.file(
            "/etc/products.d/baseproduct"
        ).linked_to == "/etc/products.d/openSUSE.prod"
    )


def test_sets_baseproduct_from_prod_files(container_per_test):
    container_per_test.run_expect(
        [0],
        """rm /etc/products.d/baseproduct
rm /etc/products.d/openSUSE.prod
touch /etc/products.d/10.prod
touch /etc/products.d/20.prod
""",
    )

    container_per_test.run_expect(
        [0], ". /bin/functions.sh && suseSetupProduct"
    )
    assert container_per_test.file("/etc/products.d/baseproduct").exists
    assert container_per_test.file("/etc/products.d/baseproduct").is_symlink
    assert (
        container_per_test.file(
            "/etc/products.d/baseproduct"
        ).linked_to == "/etc/products.d/20.prod"
    )
