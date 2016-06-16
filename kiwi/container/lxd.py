# Copyright (c) 2016 SUSE Linux GmbH.  All rights reserved.
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
import sys
import os
import io
import re
import time
import platform
import tempfile
import shutil
import tarfile

# project
from ..archive.tar import ArchiveTar
from ..defaults import Defaults
from ..utils.sync import DataSync
from ..logger import log


EXCLUDE_LIST = [
    'image',
    '.profile',
    '.kconfig',
    'boot',
    Defaults.get_shared_cache_location(),
]


class ContainerImageLxd(object):
    """
    Create LXD container from a root directory

    Attributes

    * :attr:`root_dir`
        root directory path name
    """
    def __init__(self, root_dir):
        self.root_dir = root_dir

    def create(self, filename):
        """
        Create LXD unified-tarball style artifact (as opposed to the
        split-tarball style).

        See https://github.com/lxc/lxd/blob/master/doc/image-handling.md#unified-tarball
        for further detail.  This single style affords us to leave the
        existing ContainerBuilder interface/signatures in place and also
        helps the user in having a single artifact to manage.  It also
        happens to be the recommended format from LXD folks too.

        At the time of writing, this unified tarball style takes the
        following shape:

        rootfs/  <-- where we must put our "self.root_dir"
        metadata.yaml
        templates/ (optional)

        Note that metadata.yaml and templates are to be found in the
        <description_dir>/lxd_metadata/ directory.  If it doesn't exist
        a minimal specification (dynamically created) is used.

        The metadata.yaml configuration is documented at:
        https://github.com/lxc/lxd/blob/master/doc/image-handling.md#content

        Be aware that we (kiwi) assume all ownership of the two required
        elements of metadata.yaml ("architecture: <...>" and
        "creation_date: <...>".  Existing metadata follows these
        dynamically constructed elements.

        :param string filename: target file to create
        """
        # NB: we support two styles of constructing our LXD tarball:
        # (1) the legacy mode works with all python versions but
        #     requires an extra copy of the root_dir (yuck!)
        # (2) the new mode works with py v3.3+ (built with lzma
        #     support)
        #
        # Note also that this "different branches for different
        # versions of Python" can give us coverage trouble given the
        # current setup of tox/pytest arguments.  Except that our
        # testing will be more unit-style and less end-to-end.
        # Another solution to this (and is probably a Good Idea
        # regardless) would be to rearchitect our tox/pytest setup to
        # combine coverage for every environment and use that number
        # in measuring our threshold compliance.
        creation_method = self._get_creation_method()
        if creation_method == 'new':
            self._create_new(filename)
        else:
            self._create_legacy(filename)

    def _get_creation_method(self):
        if sys.version_info >= (3, 3) and self._has_lzma():
            return 'new'
        else:
            return 'legacy'

    def _has_lzma(self):  # pragma: no cover
        try:              # ... bit tricky to cover missing imports
            import lzma
            lzma.is_check_supported(lzma.CHECK_NONE)  # to remedy "unused import" chirp
            return True
        except:
            return False

    def _get_metadata_yaml(self):
        user_metadata_yaml_path = os.path.join(
            self.root_dir,
            'image',
            'lxd_metadata',
            'metadata.yaml'
        )
        if os.path.exists(user_metadata_yaml_path):
            with io.open(user_metadata_yaml_path) as user_metadata_yaml_file:
                user_metadata_yaml_data = user_metadata_yaml_file.read()
        else:
            user_metadata_yaml_data = u''
        if re.findall(
                r'(^architecture:)|(^creation_date:)',
                user_metadata_yaml_data,
                re.MULTILINE):
            err = (
                "supplied metadata.yaml already contains either architecture "
                "or creation_date fields (that kiwi needs to control)")
            raise ValueError(err)
        metadata_yaml_header = (
            "# auto-populated by kiwi\n"
            "architecture: {arch}\n"
            "creation_date: {unixtime}\n"
            "# back to user content...\n".format(
                arch=platform.machine(),
                unixtime=int(time.time())))
        return metadata_yaml_header + user_metadata_yaml_data

    # new-style (more efficient) LXD tarball artifact creation

    def _create_new(self, filename):
        log.info("Creating LXD image (new and efficient mode)")
        compression_type = self._get_compression_type(filename)
        with tarfile.open(filename, mode='w%s' % compression_type) as archive:
            # the rootfs that we know and love from all kiwi prepares
            archive.add(
                self.root_dir,
                arcname='rootfs',
                recursive=True,
                filter=self._filter_exclusions)
            # grab the LXD metadata (yaml config plus templates)
            archive.addfile(*self._get_metadata_yaml_tarinfo_and_fileobj())
            user_metadata_templates_path = os.path.join(
                self.root_dir,
                'image',
                'lxd_metadata',
                'templates'
            )
            if os.path.isdir(user_metadata_templates_path):
                archive.add(
                    user_metadata_templates_path,
                    arcname='templates',
                    recursive=True)

    def _get_compression_type(self, filename):
        # It is unfortunate that tarfile doesn't have a "transparent
        # compression" behavior on the write-side (ala
        # "--auto-compress" on GNU tar(1)).  If ever added to tarfile,
        # please remove this helper method (TODO).
        suffix = os.path.splitext(os.path.basename(filename))[1]
        if suffix == '.tar':
            return ''
        elif suffix in ('.gz', '.tgz'):  # other shortcuts common?
            return ':gz'
        elif suffix == '.bz2':
            return ':bz2'
        elif suffix == '.xz':
            return ':xz'
        else:
            raise ValueError("unsupported file extension: %s" % suffix)

    def _filter_exclusions(self, tarinfo):
        if os.path.basename(tarinfo.name) in EXCLUDE_LIST:
            return None
        else:
            return tarinfo

    def _get_metadata_yaml_tarinfo_and_fileobj(self):
        now = int(time.time())
        data_bytes = self._get_metadata_yaml().encode('utf-8')
        fileobj = io.BytesIO(data_bytes)

        member = tarfile.TarInfo('metadata.yaml')
        member.size = len(data_bytes)
        member.mtime = now
        member.mode = 0o0644
        member.type = tarfile.REGTYPE
        member.uid = 0
        member.gid = 0
        member.uname = 'root'
        member.gname = 'root'

        return (member, fileobj)

    # old-style (less requirements on version, etc.) LXD tarball
    # artifact creation

    def _create_legacy(self, filename):
        log.info("Creating LXD image (old but more compatible mode)")
        tmpdir = tempfile.mkdtemp(
            # We use dir=... to place our potentially large data on a
            # known-large filesystem.
            dir=os.path.dirname(filename),
            prefix='tmp_kiwilxd_')
        try:
            # This approach below is slightly expensive (i.e., the
            # whole root tree is copied) but avoids (surprisingly and
            # sadly) very hairy code with reparenting TarInfo members.
            #
            # Note also that shutil.copytree chokes on device/special
            # files, thus the use DataSync (which in turn uses the
            # more robust rsync).  Because we're using rsync (thru
            # DataSync), obviously the trailing source slash is
            # meaningful.
            syncer = DataSync(self.root_dir + '/', os.path.join(tmpdir, 'rootfs'))
            syncer.sync_data(
                options=['-a', '-X', '-A'])
            self._add_lxd_metadata_legacy(tmpdir)
            archive = ArchiveTar(filename)
            archive.create(
                source_dir=tmpdir,
                # NB: the exclude= kwarg doesn't work since it currently
                #     only pertains to toplevel items (and we have
                #     rootfs/image; thus we supply our own --exclude
                #     manually.
                options=['--auto-compress', '--exclude=rootfs/image']
            )
        finally:
            shutil.rmtree(tmpdir)

    def _add_lxd_metadata_legacy(self, tmpdir):
        temp_metadata_yaml_path = os.path.join(tmpdir, 'metadata.yaml')
        temp_metadata_templates_path = os.path.join(tmpdir, 'templates')
        user_metadata_templates_path = os.path.join(
            self.root_dir,
            'image',
            'lxd_metadata',
            'templates'
        )
        with io.open(temp_metadata_yaml_path, 'w') as temp_metadata_yaml_file:
            temp_metadata_yaml_file.write(self._get_metadata_yaml())
        if os.path.isdir(user_metadata_templates_path):
            shutil.copytree(
                user_metadata_templates_path,
                temp_metadata_templates_path
            )
