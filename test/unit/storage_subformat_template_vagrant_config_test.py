from kiwi.storage.subformat.template.vagrant_config import (
    VagrantConfigTemplate
)

from textwrap import dedent


class TestVagrantConfigTemplate(object):

    def setup(self):
        self.vagrant_config = VagrantConfigTemplate()

    def test_default_Vagrantfile(self):
        Vagrantfile = dedent('''
        Vagrant.configure("2") do |config|
          config.vm.base_mac = "deadbeef"
        end
        ''').strip()
        assert self.vagrant_config.get_template()\
                                  .substitute({'mac_address': 'deadbeef'}) \
            == Vagrantfile

    def test_customized_Vagrantfile(self):
        Vagrantfile = dedent('''
        Vagrant.configure("2") do |config|
          config.vm.base_mac = "DEADBEEF"
          config.vm.hostname = "no-dead-beef"
          config.vm.provider :special do |special|
            special.secret_settings = "please_work"
          end
        end
        ''').strip()
        extra_settings = dedent('''
        config.vm.hostname = "no-dead-beef"
        config.vm.provider :special do |special|
          special.secret_settings = "please_work"
        end
        ''').strip()
        assert self.vagrant_config.get_template(extra_settings)\
                                  .substitute({'mac_address': 'DEADBEEF'}) \
            == Vagrantfile
