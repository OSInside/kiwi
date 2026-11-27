from kiwi.utils.install_progress import InstallProgress, PackageManagerEventT


class TestInstallProgress:
    def test_counted_phases(self):
        progress = InstallProgress(['download', 'install'])
        progress.update(
            PackageManagerEventT('download', 'Downloading glibc', 74, 148)
        )
        assert progress.completed == 250
        assert progress.description == '74/148 Downloading glibc'
        progress.update(
            PackageManagerEventT(
                'install', 'Installing glibc', 148, 148, package='glibc'
            )
        )
        # the progress is only complete with the end of the run
        assert progress.completed == 990
        # scripts are shown but do not change the progress
        progress.update(
            PackageManagerEventT(
                'script', 'Running %posttrans(udev)', package='%posttrans(udev)'
            )
        )
        assert progress.description == 'Running %posttrans(udev)'
        assert progress.completed == 990
        # an earlier phase does not move the progress backwards
        progress.update(
            PackageManagerEventT('download', 'Downloading bash', 1, 148)
        )
        assert progress.completed == 990
        assert progress.summary() == '1 package installed, 1 script run'

    def test_events_without_position(self):
        progress = InstallProgress(['download', 'install'])
        # without the number of packages there is no progress
        progress.update(PackageManagerEventT('install', 'Unpacking bash'))
        assert progress.completed == 0
        assert progress.description == 'Unpacking bash'
        progress.update(PackageManagerEventT('total', total=4))
        assert progress.packages_total == 4
        # the events of the phase are counted against the packages
        progress.update(
            PackageManagerEventT(
                'install', 'Unpacking coreutils', package='coreutils'
            )
        )
        assert progress.completed == 750
        assert progress.description == '2/4 Unpacking coreutils'
        progress.update(
            PackageManagerEventT(
                'install', 'Removing vim', package='vim', removed=True
            )
        )
        progress.update(
            PackageManagerEventT('script', 'Running post-transaction hooks')
        )
        assert progress.summary() == '1 package installed, 1 package removed'

    def test_no_events(self):
        progress = InstallProgress([])
        assert not progress.events_seen
        assert progress.summary() == ''
        progress.update(
            PackageManagerEventT('script', 'Running scripts', 1, 3, 'a', False)
        )
        assert progress.events_seen
        assert progress.description == '1/3 Running scripts'
        assert progress.summary() == '1 script run'
