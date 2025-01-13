from pytest import raises
import os

from kiwi.utils.toenv import ToEnv
from kiwi.exceptions import KiwiEnvImportError


class TestToEnv(object):
    def setup(self):
        ToEnv('../data', 'some.env')
        assert os.environ['ZYPP_MODALIAS_SYSFS'] == ''

    def setup_method(self, cls):
        self.setup()

    def test_setup_raises(self):
        with raises(KiwiEnvImportError):
            ToEnv('../data', 'some_broken.env')
