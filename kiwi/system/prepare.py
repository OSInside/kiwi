# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of kiwi.
#
# kiwi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi.  If not, see <http://www.gnu.org/licenses/>
#
import os

# project
from .root_init import RootInit
from .root_bind import RootBind
from ..repository import Repository
from ..package_manager import PackageManager
from ..command_process import CommandProcess
from .uri import Uri
from ..archive.tar import ArchiveTar

from ..logger import log

from ..exceptions import (
    KiwiBootStrapPhaseFailed,
    KiwiSystemUpdateFailed,
    KiwiSystemInstallPackagesFailed,
    KiwiSystemDeletePackagesFailed,
    KiwiInstallPhaseFailed
)


class SystemPrepare(object):
    """
    Implements preparation and installation of a new root system

    Attributes

    * :attr:`xml_state`
        Instance of XMLState

    * :attr:`profiles`
        list of configured profiles

    * :attr:`root_bind`
        Instance of RootBind

    * :attr:`uri_list`
        A list of Uri references
    """
    def __init__(
        self, xml_state, root_dir, allow_existing=False
    ):
        """
        Setup and host bind new root system at given root_dir directory
        """
        log.info('Setup root directory: %s', root_dir)
        root = RootInit(
            root_dir, allow_existing
        )
        root.create()
        root_bind = RootBind(
            root
        )
        root_bind.setup_intermediate_config()
        root_bind.mount_kernel_file_systems()
        root_bind.mount_shared_directory()

        self.xml_state = xml_state
        self.profiles = xml_state.profiles
        self.root_bind = root_bind

        # A list of Uri references is stored inside of the System instance
        # in order to delay the Uri destructors until the System instance
        # dies. This is needed to keep bind mounted Uri locations alive
        # for System operations
        self.uri_list = []

    def setup_repositories(self):
        """
        Set up repositories for software installation and return a
        package manager for performing software installation tasks

        :return: Instance of PackageManager
        :rtype: PackageManager
        """
        repository_options = []
        repository_sections = self.xml_state.get_repository_sections()
        package_manager = self.xml_state.get_package_manager()
        if self.xml_state.get_rpm_excludedocs():
            repository_options.append('exclude_docs')
        repo = Repository(
            self.root_bind, package_manager, repository_options
        )
        for xml_repo in repository_sections:
            repo_type = xml_repo.get_type()
            repo_source = xml_repo.get_source().get_path()
            repo_alias = xml_repo.get_alias()
            repo_priority = xml_repo.get_priority()
            repo_dist = xml_repo.get_distribution()
            repo_components = xml_repo.get_components()
            log.info('Setting up repository %s', repo_source)
            log.info('--> Type: %s', repo_type)
            if repo_priority:
                log.info('--> Priority: %s', repo_priority)

            uri = Uri(repo_source, repo_type)
            repo_source_translated = uri.translate()
            log.info('--> Translated: %s', repo_source_translated)
            if not repo_alias:
                repo_alias = uri.alias()
            log.info('--> Alias: %s', repo_alias)

            if not uri.is_remote() and not os.path.exists(
                repo_source_translated
            ):
                log.warning(
                    'repository %s does not exist and will be skipped',
                    repo_source
                )
                continue

            if not uri.is_remote():
                self.root_bind.mount_shared_directory(repo_source_translated)

            repo.add_repo(
                repo_alias, repo_source_translated,
                repo_type, repo_priority, repo_dist, repo_components
            )
            self.uri_list.append(uri)
        repo.cleanup_unused_repos()
        return PackageManager(
            repo, package_manager
        )

    def install_bootstrap(self, manager):
        """
        Install system software using the package manager
        from the host, also known as bootstrapping
        """
        log.info('Installing bootstrap packages')
        bootstrap_packages = self.xml_state.get_bootstrap_packages()
        bootstrap_packages.append(
            self.xml_state.get_package_manager()
        )
        collection_type = self.xml_state.get_bootstrap_collection_type()
        log.info('--> collection type: %s', collection_type)
        bootstrap_collections = self.xml_state.get_bootstrap_collections()
        bootstrap_products = self.xml_state.get_bootstrap_products()
        bootstrap_archives = self.xml_state.get_bootstrap_archives()
        # process package installations
        if collection_type == 'onlyRequired':
            manager.process_only_required()
        all_install_items = self._setup_requests(
            manager,
            bootstrap_packages,
            bootstrap_collections,
            bootstrap_products
        )
        process = CommandProcess(
            command=manager.process_install_requests_bootstrap(),
            log_topic='bootstrap'
        )
        try:
            process.poll_show_progress(
                items_to_complete=all_install_items,
                match_method=process.create_match_method(
                    manager.match_package_installed
                )
            )
        except Exception as e:
            raise KiwiBootStrapPhaseFailed(
                'Bootstrap package installation failed: %s' % format(e)
            )
        manager.dump_reload_package_database()
        # process archive installations
        if bootstrap_archives:
            try:
                self._install_archives(bootstrap_archives)
            except Exception as e:
                raise KiwiBootStrapPhaseFailed(
                    'Bootstrap archive installation failed: %s' % format(e)
                )

    def install_system(self, manager):
        """
        Install system software using the package manager inside
        of the new root directory. This is done via a chroot operation
        and requires the desired package manager to became installed
        via the bootstrap phase

        :param object manager: PackageManager
        """
        log.info(
            'Installing system (chroot) for build type: %s',
            self.xml_state.get_build_type_name()
        )
        collection_type = self.xml_state.get_system_collection_type()
        log.info('--> collection type: %s', collection_type)
        system_packages = self.xml_state.get_system_packages()
        system_collections = self.xml_state.get_system_collections()
        system_products = self.xml_state.get_system_products()
        system_archives = self.xml_state.get_system_archives()
        # process package installations
        if collection_type == 'onlyRequired':
            manager.process_only_required()
        all_install_items = self._setup_requests(
            manager,
            system_packages,
            system_collections,
            system_products
        )
        if all_install_items:
            process = CommandProcess(
                command=manager.process_install_requests(), log_topic='system'
            )
            try:
                process.poll_show_progress(
                    items_to_complete=all_install_items,
                    match_method=process.create_match_method(
                        manager.match_package_installed
                    )
                )
            except Exception as e:
                raise KiwiInstallPhaseFailed(
                    'System package installation failed: %s' % format(e)
                )
        # process archive installations
        if system_archives:
            try:
                self._install_archives(system_archives)
            except Exception as e:
                raise KiwiInstallPhaseFailed(
                    'System archive installation failed: %s' % format(e)
                )

    def pinch_system(self, manager, force=False):
        """
        Delete packages marked for deletion in the XML description

        :param object manager: PackageManager
        :param bool force: force deletion true|false
        """
        to_become_deleted_packages = \
            self.xml_state.get_to_become_deleted_packages()
        if to_become_deleted_packages:
            log.info('Pinch system')
            try:
                self.delete_packages(manager, to_become_deleted_packages, force)
            except Exception as e:
                raise KiwiInstallPhaseFailed(
                    '%s: %s' % (type(e).__name__, format(e))
                )

    def install_packages(self, manager, packages):
        """
        Install one or more packages using the package manager inside
        of the new root directory

        :param object manager: PackageManager
        :param list packages: package list
        """
        log.info('Installing system packages (chroot)')
        all_install_items = self._setup_requests(
            manager, packages
        )
        if all_install_items:
            process = CommandProcess(
                command=manager.process_install_requests(), log_topic='system'
            )
            try:
                process.poll_show_progress(
                    items_to_complete=all_install_items,
                    match_method=process.create_match_method(
                        manager.match_package_installed
                    )
                )
            except Exception as e:
                raise KiwiSystemInstallPackagesFailed(
                    'Package installation failed: %s' % format(e)
                )

    def delete_packages(self, manager, packages, force=False):
        """
        Delete one or more packages using the package manager inside
        of the new root directory

        :param object manager: PackageManager
        :param list packages: package list
        :param bool force: force deletion true|false
        """
        log.info('Deleting system packages (chroot)')
        all_delete_items = self._setup_requests(
            manager, packages
        )
        if all_delete_items:
            process = CommandProcess(
                command=manager.process_delete_requests(force),
                log_topic='system'
            )
            try:
                process.poll_show_progress(
                    items_to_complete=all_delete_items,
                    match_method=process.create_match_method(
                        manager.match_package_deleted
                    )
                )
            except Exception as e:
                raise KiwiSystemDeletePackagesFailed(
                    'Package deletion failed: %s' % format(e)
                )

    def update_system(self, manager):
        """
        Install package updates from the used repositories.
        the process uses the package manager from inside of the
        new root directory

        :param object manager: PackageManager
        """
        log.info('Update system (chroot)')
        process = CommandProcess(
            command=manager.update(), log_topic='update'
        )
        try:
            process.poll()
        except Exception as e:
            raise KiwiSystemUpdateFailed(
                'System update failed: %s' % format(e)
            )

    def _install_archives(self, archive_list):
        log.info("Installing archives")
        for archive in archive_list:
            log.info("--> archive: %s", archive)
            description_dir = \
                self.xml_state.xml_data.description_dir
            derived_description_dir = \
                self.xml_state.xml_data.derived_description_dir
            archive_is_absolute = archive.startswith('/')
            if archive_is_absolute:
                archive_file = archive
            else:
                archive_file = '/'.join(
                    [description_dir, archive]
                )
            archive_exists = os.path.exists(archive_file)
            if not archive_is_absolute and not archive_exists and derived_description_dir:
                archive_file = '/'.join(
                    [derived_description_dir, archive]
                )
            tar = ArchiveTar(archive_file)
            tar.extract(self.root_bind.root_dir)

    def _setup_requests(
        self, manager, packages, collections=None, products=None
    ):
        if packages:
            for package in sorted(packages):
                log.info('--> package: %s', package)
                manager.request_package(package)
        if collections:
            for collection in sorted(collections):
                log.info('--> collection: %s', collection)
                manager.request_collection(collection)
        if products:
            for product in sorted(products):
                log.info('--> product: %s', product)
                manager.request_product(product)
        return \
            manager.package_requests + \
            manager.collection_requests + \
            manager.product_requests

    def __del__(self):
        log.info('Cleaning up %s instance', type(self).__name__)
        try:
            self.root_bind.cleanup()
        except Exception:
            pass
