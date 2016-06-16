
from mock import patch

from kiwi.container.setup.lxd import ContainerSetupLxd


class TestContainerSetupLxd(object):
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        self.container = ContainerSetupLxd('root_dir', {})

    def test_setup(self):
        # Nothing to really test as LXD setup is, at present,
        # effectively a stub.  So this is for coverage now (didn't
        # pragma-no-cover this as we may someday use this; e.g., to
        # populate the LXD metadata).
        self.container.setup()
