Write Integration Tests for the Scripts
---------------------------------------

{kiwi} comes with a set of helper functions that can be used in :file:`config.sh` (see
also: :ref:`working-with-kiwi-user-defined-scripts`). These functions utilize containers
to run the individual tasks and verify the final result.

Ensure that you have either :command:`podman` or :command:`docker` installed and
configured on your system. With Podman, the integration tests use :command:`podman` in
**rootless mode** by default. You can select
:command:`docker` instead by setting the environment variable
``CONTAINER_RUNTIME`` to ``docker``. Then you can run the integration tests via
tox:

.. code:: shell-session

    $ tox -e scripts -- -n NUMBER_OF_THREADS


The tests are written using the `pytest-container
<https://github.com/dcermak/pytest_container>`__ plugin. If applicable,
use the utility functions and fixtures of the plugin. For example, the
``auto_container`` and ``auto_container_per_test`` fixtures in conjunction with
`testinfra <https://testinfra.readthedocs.io/>`__.


Test setup
~~~~~~~~~~

The script tests can be run inside different containers specified in
:file:`test/scripts/conftest.py`. This file contains the ``CONTAINERS`` list
with all currently present images. These images are pulled and built as needed,
and the :file:`functions.sh` is copied into :file:`/bin/`, so it is
available in ``PATH``.

To use any of these containers, you can either define the global variable
``CONTAINER_IMAGES`` in a test module and use the ``auto_container`` fixture, or
`parametrize <https://docs.pytest.org/en/stable/parametrize.html>`__ the
``container`` fixture indirectly:

.. code:: python

    @pytest.mark.parametrize("container_per_test", (TUMBLEWEED, LEAP_15_3), indirect=True)
    def test_RmWorks(container_per_test):
        # create the file /root/foobar
        container_per_test.connection.run_expect([0], "touch /root/foobar")
        assert container_per_test.connection.file("/root/foobar").exists

        # source the functions and execute our function under test
        container_per_test.connection.run_expect([0], ". /bin/functions.sh && Rm /root/foobar")

        # verify the result
        assert not container_per_test.connection.file("/root/foobar").exists


The example above uses the ``_per_test`` variant of the ``container`` fixture.
It ensures that the container is used only in a single test function. Use this
variant for tests that mutate the system under test, because otherwise it may
lead race conditions that are difficult to debug. For tests that only perform
reads, you can omit the ``_per_test`` suffix, so that the container environment can
shared with other tests. This improves execution speed, but comes at the
expense of safety in case of mutation.

For further information, refer to `pytest-container
<https://github.com/dcermak/pytest_container>`__.
