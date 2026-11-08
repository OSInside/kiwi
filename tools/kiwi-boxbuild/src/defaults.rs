// Copyright (c) 2026 SUSE Software Solutions Germany GmbH.  All rights reserved.
//
// This file is part of kiwi.
//
// kiwi is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// kiwi is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with kiwi.  If not, see <http://www.gnu.org/licenses/>
//
pub const PODMAN_PATH: &str =
    "/usr/bin/podman";

// Container which provides kiwi and the requirements of the
// kiwi-ng system boxbuild command, see the runtime_container
// setting in the boxbuild section of the kiwi runtime config
pub const RUNTIME_CONTAINER: &str =
    "registry.opensuse.org/virtualization/appliances/selfcontained/runtime/images/boxbuild:latest";

// Locations of the build in the runtime container. The image
// description and the target directory are mounted from the host.
// The boxes are stored on the host and mounted to the location
// kiwi stores them at in the runtime container
pub const KIWI_DESCRIPTION_DIR: &str =
    "/description";
pub const KIWI_TARGET_DIR: &str =
    "/result";
pub const KIWI_BOXES_DIR: &str =
    "/root/.kiwi_boxes";
pub const KIWI_BOXES_CONFIG_FILE: &str =
    "/etc/kiwi_boxed_plugin.yml";

// Location of the boxes on the host, the same as used by
// kiwi-ng system boxbuild: $KIWI_BOXED_CACHE_DIR if set to an
// existing directory, otherwise $HOME/.kiwi_boxes
pub const KIWI_BOXES_NAME: &str =
    ".kiwi_boxes";
pub const KIWI_BOXES_DIR_ENV: &str =
    "KIWI_BOXED_CACHE_DIR";

// Files the box stores in the target directory: the exit code
// of the build in the box and the log of the build
pub const KIWI_RESULT_CODE_NAME: &str =
    "result.code";
pub const KIWI_RESULT_LOG_NAME: &str =
    "result.log";

// kiwi runtime config files in the order kiwi reads them, a
// setting in a later file takes precedence. The user config is
// located below the home directory
pub const USR_RUNTIME_CONFIG_FILE: &str =
    "/usr/share/kiwi/kiwi.yml";
pub const USR_RUNTIME_CONFIG_DIR: &str =
    "/usr/share/kiwi/kiwi.yml.d";
pub const ETC_RUNTIME_CONFIG_FILE: &str =
    "/etc/kiwi.yml";
pub const ETC_RUNTIME_CONFIG_DIR: &str =
    "/etc/kiwi.yml.d";
pub const USER_RUNTIME_CONFIG_FILE: &str =
    ".config/kiwi/config.yml";
