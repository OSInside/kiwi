Write Integration Tests for the Scripts
---------------------------------------

Kiwi ships a set of helper functions that can be used in :file:`config.sh` (see
also: :ref:`working-with-kiwi-user-defined-scripts`). These utilize containers
to run the individual functions and verify that they resulted in the desired
state.

Ensure that you have either :command:`podman` or :command:`docker` installed and
configured on your system. The integration tests will use :command:`podman` in
**rootless mode** by default, if it is installed on your system. You can select
:command:`docker` instead by setting the environment variable
``CONTAINER_RUNTIME`` to ``docker``. Then you can run the integration tests via
tox:

.. code:: shell-session

    $ tox -e scripts -- -n NUMBER_OF_THREADS


It is recommended to leverage `testinfra <https://testinfra.readthedocs.io/>`__
and the ``shared_container`` and ``container_per_test`` fixtures for writing
these integration tests. The fixtures give your test functions a connection to a
running container (by default that will be ``opensuse/tumbleweed``)
:file:`functions.sh` copied to :file:`/bin/functions.sh` inside the
container. You can then use the connection to perform some setup, tear down and
the actual tests as follows:

.. code:: python

    def test_RmWorks(shared_container):
        # create the file /root/foobar
        shared_container.run_expect([0], "touch /root/foobar")
        assert shared_container.file("/root/foobar").exists

        # source the functions and execute our function under test
        shared_container.run_expect([0], ". /bin/functions.sh && Rm /root/foobar")

        # verify the result
        assert not shared_container.file("/root/foobar").exists


In this example we used the ``shared_container`` fixture: it creates a podman
container at the start of the test session and gives each function using this
fixture the same connection. Therefore you must only use it for tests where you
do not perform any mutation of the container that you are not undoing
afterwards! If you need to perform extensive mutation that you cannot or do not
want to undo yourself, then resort to the ``container_per_test`` fixture. It
will give you a fresh container for each test function. While this makes writing
tests simpler, it also increases the runtime significantly, thus only use it
when necessary.


Running Tests for multiple container images
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is important to test certain functions on multiple operating systems &
versions, to e.g. ensure that older tools behave the same way that you expect
them to.

This can be achieved by leveraging pytest's `fixture parametrization
<https://docs.pytest.org/en/stable/parametrize.html>`__ as follows:

.. code:: python

    @pytest.mark.parametrize(
        "shared_container",
        (
            "Tumbleweed",
            "Leap-{exc_os_version}",
        ),
        indirect=True,
    )
    def test_something(shared_container):
        pass


Where we pass multiple image names to the container images to the
``shared_container`` fixture. Pytest will then look for the image with the given
name in the predefined list of containers in :file:`conftest.py`.

To add a new container, simply add a new ``Container`` class to the
``CONTAINERS`` list and give it appropriate values for ``name`` and ``url``.
