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
import logging
from typing import (
    List, Any, Optional
)
from textwrap import dedent

# project
from kiwi.xml_parse import repository
from kiwi.xml_state import XMLState
from kiwi.system.root_init import RootInit
from kiwi.system.root_import import RootImport
from kiwi.system.root_bind import RootBind
from kiwi.repository import Repository
from kiwi.package_manager import PackageManager
from kiwi.package_manager.base import PackageManagerBase
from kiwi.command_process import CommandProcess
from kiwi.system.uri import Uri
from kiwi.archive.tar import ArchiveTar

from kiwi.exceptions import (
    KiwiBootStrapPhaseFailed,
    KiwiSystemUpdateFailed,
    KiwiSystemInstallPackagesFailed,
    KiwiSystemDeletePackagesFailed,
    KiwiInstallPhaseFailed,
    KiwiPackagesDeletePhaseFailed
)

log: Any = logging.getLogger('kiwi')


class SystemPrepare:
    """
    Implements preparation and installation of a new root system

    :param object xml_state: instance of :class:`XMLState`
    :param str root_dir: Path to new root directory
    :param bool allow_existing: Allow using an existing root_dir
    """
    def __init__(
        self, xml_state: XMLState, root_dir: str, allow_existing: bool = False
    ):
        """
        Setup and host bind new root system at given root_dir directory
        """
        log.info('Setup root directory: %s', root_dir)
        if not log.getLogLevel() == logging.DEBUG and not log.get_logfile():
            self.issue_message = dedent('''
                {headline}: {reason}

                Further details to clarify the error might have been
                reported earlier in the package manager log information
                and did not get exposed to the caller. Thus if the above
                message is not clear on the error please call kiwi with
                the --debug or --logfile option.
            ''')
        else:
            self.issue_message = '{headline}: {reason}'
        root = RootInit(
            root_dir, allow_existing
        )
        root.create()
        image_uri = xml_state.get_derived_from_image_uri()
        if image_uri:
            root_import = RootImport.new(
                root_dir, image_uri, xml_state.build_type.get_image()
            )
            root_import.sync_data()
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
        self.uri_list: List[Uri] = []

    def setup_repositories(
        self, clear_cache: bool = False,
        signing_keys: List[str] = None, target_arch: Optional[str] = None
    ) -> PackageManagerBase:
        """
        Set up repositories for software installation and return a
        package manager for performing software installation tasks

        :param bool clear_cache:
            Flag the clear cache before configure anything
        :param list signing_keys:
            Keys imported to the package manager
        :param str target_arch:
            Target architecture name

        :return: instance of :class:`PackageManager` subclass

        :rtype: PackageManager
        """
        repository_options = []
        repository_sections = \
            self.xml_state.get_repository_sections_used_for_build()
        package_manager = self.xml_state.get_package_manager()
        rpm_locale_list = self.xml_state.get_rpm_locale()
        if self.xml_state.get_rpm_check_signatures():
            repository_options.append('check_signatures')
        if self.xml_state.get_rpm_excludedocs():
            repository_options.append('exclude_docs')
        if rpm_locale_list:
            repository_options.append(
                '_install_langs%{0}'.format(':'.join(rpm_locale_list))
            )
        if target_arch:
            repository_options.append(
                f'_target_arch%{target_arch}'
            )
        repo = Repository.new(
            self.root_bind, package_manager, repository_options
        )
        repo.setup_package_database_configuration()
        if signing_keys:
            repo.import_trusted_keys(signing_keys)
        for xml_repo in repository_sections:
            repo_type = xml_repo.get_type()
            repo_source = xml_repo.get_source().get_path()
            repo_user = xml_repo.get_username()
            repo_secret = xml_repo.get_password()
            repo_alias = xml_repo.get_alias()
            repo_priority = xml_repo.get_priority()
            repo_dist = xml_repo.get_distribution()
            repo_components = xml_repo.get_components()
            repo_repository_gpgcheck = xml_repo.get_repository_gpgcheck()
            repo_package_gpgcheck = xml_repo.get_package_gpgcheck()
            repo_customization_script = self._get_repo_customization_script(
                xml_repo
            )
            repo_sourcetype = xml_repo.get_sourcetype()
            repo_use_for_bootstrap = \
                True if xml_repo.get_use_for_bootstrap() else False
            log.info('Setting up repository %s', repo_source)
            log.info('--> Type: {0}'.format(repo_type))
            if repo_sourcetype:
                log.info('--> SourceType: {0}'.format(repo_sourcetype))
            if repo_priority:
                log.info('--> Priority: {0}'.format(repo_priority))

            uri = Uri(repo_source, repo_type)
            repo_source_translated = uri.translate()
            log.info('--> Translated: {0}'.format(repo_source_translated))
            if not repo_alias:
                repo_alias = uri.alias()
            log.info('--> Alias: {0}'.format(repo_alias))

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
                repo_type, repo_priority, repo_dist, repo_components,
                repo_user, repo_secret, uri.credentials_file_name(),
                repo_repository_gpgcheck, repo_package_gpgcheck,
                repo_sourcetype, repo_use_for_bootstrap,
                repo_customization_script
            )
            if clear_cache:
                repo.delete_repo_cache(repo_alias)
            self.uri_list.append(uri)
        repo.cleanup_unused_repos()
        return PackageManager.new(
            repo, package_manager
        )

    def install_bootstrap(
        self, manager: PackageManagerBase, plus_packages: List = None
    ) -> None:
        """
        Install system software using the package manager
        from the host, also known as bootstrapping

        :param object manager: instance of a :class:`PackageManager` subclass
        :param list plus_packages: list of additional packages

        :raises KiwiBootStrapPhaseFailed:
            if the bootstrapping process fails either installing
            packages or including bootstrap archives
        """
        if not self.xml_state.get_bootstrap_packages_sections() \
           and not plus_packages:
            log.warning('No <packages> sections marked as "bootstrap" found')
            log.info('Processing of bootstrap stage skipped')
            return

        log.info('Installing bootstrap packages')
        bootstrap_packages = self.xml_state.get_bootstrap_packages(
            plus_packages
        )
        collection_type = self.xml_state.get_bootstrap_collection_type()
        log.info('--> collection type: %s', collection_type)
        bootstrap_collections = self.xml_state.get_bootstrap_collections()
        bootstrap_products = self.xml_state.get_bootstrap_products()
        bootstrap_archives = self.xml_state.get_bootstrap_archives()
        bootstrap_archives_target_dirs = self.xml_state.get_bootstrap_archives_target_dirs()
        # process package installations
        if collection_type == 'onlyRequired':
            manager.process_only_required()
        else:
            manager.process_plus_recommended()
        all_install_items = self._setup_requests(
            manager,
            bootstrap_packages,
            bootstrap_collections,
            bootstrap_products
        )
        process = CommandProcess(
            command=manager.process_install_requests_bootstrap(self.root_bind),
            log_topic='bootstrap'
        )
        try:
            process.poll_show_progress(
                items_to_complete=all_install_items,
                match_method=process.create_match_method(
                    manager.match_package_installed
                )
            )
        except Exception as issue:
            if manager.has_failed(process.returncode()):
                raise KiwiBootStrapPhaseFailed(
                    self.issue_message.format(
                        headline='Bootstrap package installation failed',
                        reason=issue
                    )
                )
        manager.post_process_install_requests_bootstrap(self.root_bind)
        # process archive installations
        if bootstrap_archives:
            try:
                self._install_archives(
                    bootstrap_archives, bootstrap_archives_target_dirs
                )
            except Exception as issue:
                raise KiwiBootStrapPhaseFailed(
                    self.issue_message.format(
                        headline='Bootstrap archive installation failed',
                        reason=issue
                    )
                )

    def install_system(self, manager: PackageManagerBase) -> None:
        """
        Install system software using the package manager inside
        of the new root directory. This is done via a chroot operation
        and requires the desired package manager to became installed
        via the bootstrap phase

        :param object manager: instance of a :class:`PackageManager` subclass

        :raises KiwiInstallPhaseFailed:
            if the install process fails either installing
            packages or including any archive
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
        system_archives_target_dirs = self.xml_state.get_system_archives_target_dirs()
        system_packages_ignored = self.xml_state.get_system_ignore_packages()
        # process package installations
        if collection_type == 'onlyRequired':
            manager.process_only_required()
        else:
            manager.process_plus_recommended()
        all_install_items = self._setup_requests(
            manager,
            system_packages,
            system_collections,
            system_products,
            system_packages_ignored
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
            except Exception as issue:
                if manager.has_failed(process.returncode()):
                    raise KiwiInstallPhaseFailed(
                        self.issue_message.format(
                            headline='System package installation failed',
                            reason=issue
                        )
                    )
        # process archive installations
        if system_archives:
            try:
                self._install_archives(
                    system_archives,
                    system_archives_target_dirs
                )
            except Exception as issue:
                raise KiwiInstallPhaseFailed(
                    self.issue_message.format(
                        headline='System archive installation failed',
                        reason=issue
                    )
                )

    def pinch_system(
        self, manager: PackageManagerBase = None, force: bool = False
    ) -> None:
        """
        Delete packages marked for deletion in the XML description. If force
        param is set to False uninstalls packages marked with
        `type="uninstall"` if any; if force is set to True deletes packages
        marked with `type="delete"` if any.

        :param object manager: instance of :class:`PackageManager` subclass
        :param bool force: Forced deletion True|False

        :raises KiwiPackagesDeletePhaseFailed:
            if the deletion packages process fails
        """
        to_become_deleted_packages = \
            self.xml_state.get_to_become_deleted_packages(force)
        if to_become_deleted_packages:
            log.info(
                '{0} system packages (chroot)'.format(
                    'Force deleting' if force else 'Uninstalling'
                )
            )
            try:
                if manager is None:
                    package_manager = self.xml_state.get_package_manager()
                    manager = PackageManager.new(
                        Repository.new(self.root_bind, package_manager),
                        package_manager
                    )
                self.delete_packages(
                    manager, to_become_deleted_packages, force
                )
            except Exception as issue:
                raise KiwiPackagesDeletePhaseFailed(
                    self.issue_message.format(
                        headline='System package deletion failed',
                        reason=issue
                    )
                )

    def install_packages(
        self, manager: PackageManagerBase, packages: List
    ) -> None:
        """
        Install one or more packages using the package manager inside
        of the new root directory

        :param object manager: instance of a :class:`PackageManager` subclass
        :param list packages: package list

        :raises KiwiSystemInstallPackagesFailed: if installation process fails
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
            except Exception as issue:
                raise KiwiSystemInstallPackagesFailed(
                    self.issue_message.format(
                        headline='Package installation failed',
                        reason=issue
                    )
                )

    def delete_packages(
        self, manager: PackageManagerBase, packages: List, force: bool = False
    ) -> None:
        """
        Delete one or more packages using the package manager inside
        of the new root directory. If the removal is set with `force` flag
        only listed packages are deleted and any dependency break or leftover
        is ignored.

        :param object manager: instance of a :class:`PackageManager` subclass
        :param list packages: package list
        :param bool force: force deletion true|false

        :raises KiwiSystemDeletePackagesFailed: if installation process fails
        """
        all_delete_items = self._setup_requests(
            manager, packages
        )
        if all_delete_items:
            log.info(
                '{0} system packages (chroot)'.format(
                    'Force deleting' if force else 'Uninstall'
                )
            )
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
            except Exception as issue:
                raise KiwiSystemDeletePackagesFailed(
                    self.issue_message.format(
                        headline='Package deletion failed',
                        reason=issue
                    )
                )

    def update_system(self, manager: PackageManagerBase) -> None:
        """
        Install package updates from the used repositories.
        the process uses the package manager from inside of the
        new root directory

        :param object manager: instance of a :class:`PackageManager` subclass

        :raises KiwiSystemUpdateFailed: if packages update fails
        """
        log.info('Update system (chroot)')
        process = CommandProcess(
            command=manager.update(), log_topic='update'
        )
        try:
            process.poll()
        except Exception as issue:
            raise KiwiSystemUpdateFailed(
                self.issue_message.format(
                    headline='System update failed',
                    reason=issue
                )
            )

    def clean_package_manager_leftovers(self) -> None:
        """
        This methods cleans some package manager artifacts created
        at run time such as macros
        """
        package_manager = self.xml_state.get_package_manager()
        manager = PackageManager.new(
            Repository.new(self.root_bind, package_manager),
            package_manager
        )
        manager.clean_leftovers()

    def _install_archives(self, archive_list, archive_target_dir_dict):
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
            if not archive_is_absolute \
               and not archive_exists and derived_description_dir:
                archive_file = '/'.join(
                    [derived_description_dir, archive]
                )
            target_dir = self.root_bind.root_dir
            if archive_target_dir_dict.get(archive):
                target_dir = os.path.join(
                    target_dir,
                    archive_target_dir_dict.get(archive)
                )
            log.info('--> target dir: %s', target_dir)
            tar = ArchiveTar(archive_file)
            tar.extract(target_dir)

    def _setup_requests(
        self, manager, packages, collections=None, products=None, ignored=None
    ):
        if packages:
            for package in sorted(packages):
                log.info('--> package: {0}'.format(package))
                manager.request_package(package)
        if collections:
            for collection in sorted(collections):
                log.info('--> collection: {0}'.format(collection))
                manager.request_collection(collection)
        if products:
            for product in sorted(products):
                log.info('--> product: {0}'.format(product))
                manager.request_product(product)
        if ignored:
            for package in sorted(ignored):
                log.info('--> package excluded: {0}'.format(package))
                manager.request_package_exclusion(package)
        return \
            manager.package_requests + \
            manager.collection_requests + \
            manager.product_requests + \
            manager.exclude_requests

    def _get_repo_customization_script(self, xml_repo: repository) -> str:
        script_path = xml_repo.get_customize()
        if script_path and not os.path.isabs(script_path):
            script_path = os.path.join(
                self.xml_state.xml_data.description_dir, script_path
            )
        return script_path

    def __del__(self):
        log.info('Cleaning up {:s} instance'.format(type(self).__name__))
        try:
            if hasattr(self, 'root_bind'):
                self.root_bind.cleanup()
        except Exception as exc:
            log.info(
                'Cleaning up {self_name:s} instance failed, got an exception '
                'of type {exc_type:s}: {exc:s}'
                .format(
                    self_name=type(self).__name__,
                    exc_type=type(exc).__name__,
                    exc=str(exc)
                )
            )
