import yaml
from unittest.mock import patch
from pytest import raises

from kiwi.boxbuild.boxes_config import BoxesConfig
from kiwi.exceptions import KiwiBoxConfigError


class TestBoxesConfig:
    @patch('kiwi.boxbuild.defaults.BoxBuildDefaults.get_box_config_file')
    def setup(self, mock_get_box_config_file):
        mock_get_box_config_file.return_value = \
            '../data/boxbuild/kiwi_boxed_plugin.yml'
        self.plugin_config = BoxesConfig()

    @patch('kiwi.boxbuild.defaults.BoxBuildDefaults.get_box_config_file')
    def setup_method(self, cls, mock_get_box_config_file):
        self.setup()

    @patch('kiwi.boxbuild.defaults.BoxBuildDefaults.get_box_config_file')
    def test_invalid_config(self, mock_get_box_config_file):
        mock_get_box_config_file.return_value = \
            '../data/boxbuild/kiwi_boxed_plugin_invalid.yml'
        with raises(KiwiBoxConfigError):
            BoxesConfig()

    def test_get_config(self):
        assert self.plugin_config.get_config() == [
            {
                'name': 'suse',
                'mem_mb': '8096M',
                'processors': 4,
                'console': 'hvc0',
                'arch': [
                    {
                        'name': 'x86_64',
                        'cmdline': ['root=/dev/vda1', 'rd.plymouth=0'],
                        'source':
                            'obs://Virtualization:Appliances:SelfContained:'
                            'suse/images',
                        'packages_file':
                            'SUSE-Box.x86_64-1.42.1-System-BuildBox.report',
                        'boxfiles': [
                            'SUSE-Box.x86_64-1.42.1-Kernel-BuildBox.tar.xz',
                            'SUSE-Box.x86_64-1.42.1-System-BuildBox.qcow2'
                        ],
                        'container': 'some',
                        'use_initrd': True
                    }
                ]
            },
            {
                'name': 'universal',
                'mem_mb': '8096M',
                'processors': 4,
                'console': 'hvc0',
                'arch': [
                    {
                        'name': 'x86_64',
                        'cmdline': [
                            'root=/dev/vda3', 'rd.plymouth=0', 'selinux=0'
                        ],
                        'source':
                            'obs://Virtualization:Appliances:SelfContained:'
                            'universal/images',
                        'packages_file':
                            'Universal-Box.x86_64-1.1.2-System-BuildBox.report',
                        'boxfiles': [
                            'Universal-Box.x86_64-1.1.2-Kernel-BuildBox.tar.xz',
                            'Universal-Box.x86_64-1.1.2-System-BuildBox.qcow2'
                        ],
                        'container': 'some',
                        'use_initrd': True
                    },
                    {
                        'name': 'aarch64',
                        'cmdline': [
                            'root=/dev/vda2', 'rd.plymouth=0', 'selinux=0'
                        ],
                        'source':
                            'obs://Virtualization:Appliances:SelfContained:'
                            'universal/images',
                        'packages_file': 'Universal-Box.'
                            'aarch64-1.1.2-System-BuildBox.report',
                        'boxfiles': [
                            'Universal-Box.aarch64-1.1.2-'
                            'Kernel-BuildBox.tar.xz',
                            'Universal-Box.aarch64-1.1.2-'
                            'System-BuildBox.qcow2'
                        ],
                        'container': 'some',
                        'use_initrd': True
                    }
                ]
            }
        ]

    def test_dump_config(self):
        assert self.plugin_config.dump_config() == yaml.dump(
            self.plugin_config.get_config()
        )

    @patch('yaml.safe_load')
    def test_setup_raises(self, mock_yaml_safe_load):
        mock_yaml_safe_load.side_effect = Exception
        with raises(KiwiBoxConfigError):
            BoxesConfig()
