from kiwi.stackbuild.defaults import StackBuildDefaults


class TestStackBuildDefaults:
    def test_get_stash_home(self):
        assert StackBuildDefaults.get_stash_home() == '/var/tmp/kiwi-stash'

    def test_is_container_name_valid(self):
        assert StackBuildDefaults.is_container_name_valid(
            'foo'
        ) is True
        assert StackBuildDefaults.is_container_name_valid(
            'Leap-15.3_appliance'
        ) is False

    def test_get_stash_exclude_list(self):
        assert StackBuildDefaults.get_stash_exclude_list() == [
            'dev/*', 'sys/*', 'proc/*'
        ]
