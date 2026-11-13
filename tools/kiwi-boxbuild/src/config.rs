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
use serde::Deserialize;
use std::fs;
use std::path::{Path, PathBuf};

use crate::defaults;

/// The part of the kiwi runtime config used by kiwi-boxbuild,
/// all other sections are ignored
///
/// boxbuild:
///   runtime_container: ...
///   runtime_wsl_image: ...
#[derive(Debug, Default, Deserialize)]
struct RuntimeConfig {
    boxbuild: Option<BoxbuildConfig>,
}

#[derive(Debug, Default, Deserialize)]
struct BoxbuildConfig {
    runtime_container: Option<String>,
    runtime_wsl_image: Option<String>,
}

/// The runtime settings of kiwi-boxbuild
#[derive(Debug, PartialEq)]
pub struct RuntimeSettings {
    /// The runtime container used with podman on Linux
    pub container: String,
    /// The WSL2 image of the runtime used on Windows, a URL or a
    /// file. None selects the default image for the host
    pub wsl_image: Option<String>,
}

pub fn get_runtime_settings(
    custom_config_file: Option<&str>
) -> Result<RuntimeSettings, String> {
    /*!
    Provide the runtime container to run the build in on Linux and
    the WSL2 image of the runtime to run the build in on Windows

    The runtime config files are read in the same order as kiwi
    reads them, a setting in a later file takes precedence. Without
    a setting defaults::RUNTIME_CONTAINER is used, and the default
    WSL2 image for the host. On Windows the user config is located
    below %USERPROFILE% if HOME is not set
    !*/
    let home = ["HOME", "USERPROFILE"].iter()
        .filter_map(|variable| std::env::var(variable).ok())
        .find(|home| ! home.is_empty());
    let config_files = runtime_config_files(
        Path::new(defaults::USR_RUNTIME_CONFIG_FILE),
        Path::new(defaults::USR_RUNTIME_CONFIG_DIR),
        Path::new(defaults::ETC_RUNTIME_CONFIG_FILE),
        Path::new(defaults::ETC_RUNTIME_CONFIG_DIR),
        home.map(|home| {
            Path::new(&home).join(defaults::USER_RUNTIME_CONFIG_FILE)
        }).as_deref(),
        custom_config_file.map(Path::new)
    )?;
    let mut settings = RuntimeSettings {
        container: defaults::RUNTIME_CONTAINER.to_string(),
        wsl_image: None
    };
    for config_file in config_files {
        let config = read_boxbuild_config(&config_file)?;
        if let Some(value) = config.runtime_container {
            debug!(
                "Runtime container {value} from {}", config_file.display()
            );
            settings.container = value;
        }
        if let Some(value) = config.runtime_wsl_image {
            debug!(
                "Runtime WSL2 image {value} from {}", config_file.display()
            );
            settings.wsl_image = Some(value);
        }
    }
    Ok(settings)
}

fn runtime_config_files(
    usr_file: &Path, usr_dir: &Path, etc_file: &Path, etc_dir: &Path,
    user_file: Option<&Path>, custom_file: Option<&Path>
) -> Result<Vec<PathBuf>, String> {
    /*!
    Provide the existing runtime config files in reading order:

    1. vendor: /usr/share/kiwi/kiwi.yml + yml files in /usr/share/kiwi/kiwi.yml.d
    2. admin: /etc/kiwi.yml + yml files in /etc/kiwi.yml.d
    3. user: ~/.config/kiwi/config.yml
    4. custom: --config FILE, which has to exist

    !*/
    let mut config_files = Vec::new();
    for (config_file, config_dir) in [(usr_file, usr_dir), (etc_file, etc_dir)] {
        if config_file.is_file() {
            config_files.push(config_file.to_path_buf());
        }
        config_files.extend(drop_in_files(config_dir));
    }
    if let Some(user_file) = user_file {
        if user_file.is_file() {
            config_files.push(user_file.to_path_buf());
        }
    }
    if let Some(custom_file) = custom_file {
        if ! custom_file.is_file() {
            return Err(format!(
                "Custom config file {} not found", custom_file.display()
            ))
        }
        config_files.push(custom_file.to_path_buf());
    }
    Ok(config_files)
}

fn drop_in_files(config_dir: &Path) -> Vec<PathBuf> {
    /*!
    Provide the yml files of the given drop-in directory sorted
    by name, nothing if the directory does not exist
    !*/
    let mut config_files: Vec<PathBuf> = match fs::read_dir(config_dir) {
        Ok(entries) => entries
            .filter_map(|entry| entry.ok())
            .map(|entry| entry.path())
            .filter(|path| {
                path.extension().is_some_and(|extension| extension == "yml")
            })
            .collect(),
        Err(_) => Vec::new()
    };
    config_files.sort();
    config_files
}

fn read_boxbuild_config(config_file: &Path) -> Result<BoxbuildConfig, String> {
    /*!
    Read the boxbuild settings from the given runtime config file,
    a setting which is not set or empty is None
    !*/
    let data = fs::read_to_string(config_file).map_err(|error| {
        format!("Failed to read {}: {error}", config_file.display())
    })?;
    // A file without any setting, e.g all commented out, is a
    // valid runtime config file
    let config: Option<RuntimeConfig> = serde_norway::from_str(&data)
        .map_err(|error| {
            format!(
                "Invalid runtime config file {}: {error}", config_file.display()
            )
        })?;
    let boxbuild = config.unwrap_or_default().boxbuild.unwrap_or_default();
    Ok(BoxbuildConfig {
        runtime_container: boxbuild.runtime_container
            .filter(|value| ! value.is_empty()),
        runtime_wsl_image: boxbuild.runtime_wsl_image
            .filter(|value| ! value.is_empty()),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::test_helper::TestDir;

    #[test]
    fn test_read_runtime_container() {
        let tmp_dir = TestDir::new();
        let config_file = tmp_dir.path().join("kiwi.yml");
        for (data, expected) in [
            // not set
            ("", None),
            ("# all settings commented out\n", None),
            ("xz:\n  options: -a\n", None),
            ("boxbuild:\n", None),
            ("boxbuild:\n  # runtime_container: foo\n", None),
            // set, other sections and comments are ignored
            (
                "obs:\n  public: true\nboxbuild:\n  # comment\n  \
                runtime_container: \"registry.example.com/box:1\"  # tag\n",
                Some("registry.example.com/box:1")
            ),
            (
                "boxbuild: {runtime_container: registry.example.com/box}\n",
                Some("registry.example.com/box")
            ),
        ] {
            fs::write(&config_file, data).unwrap();
            assert_eq!(
                read_boxbuild_config(&config_file).unwrap()
                    .runtime_container.as_deref(),
                expected, "{data}"
            );
        }
        // invalid yaml or setting
        for data in [
            "boxbuild:\n  runtime_container: [a\n",
            "boxbuild:\n  runtime_container:\n    nested: a\n",
        ] {
            fs::write(&config_file, data).unwrap();
            assert!(read_boxbuild_config(&config_file).is_err(), "{data}");
        }
        assert!(
            read_boxbuild_config(&tmp_dir.path().join("missing")).is_err()
        );
    }

    #[test]
    fn test_read_runtime_wsl_image() {
        let tmp_dir = TestDir::new();
        let config_file = tmp_dir.path().join("kiwi.yml");
        for (data, expected) in [
            ("boxbuild:\n  runtime_container: box\n", None),
            ("boxbuild:\n  runtime_wsl_image: \"\"\n", None),
            (
                "boxbuild:\n  runtime_wsl_image: https://example.com/b.wsl\n",
                Some("https://example.com/b.wsl")
            ),
            (
                "boxbuild:\n  runtime_wsl_image: 'C:\\images\\b.wsl'\n",
                Some(r"C:\images\b.wsl")
            ),
        ] {
            fs::write(&config_file, data).unwrap();
            assert_eq!(
                read_boxbuild_config(&config_file).unwrap()
                    .runtime_wsl_image.as_deref(),
                expected, "{data}"
            );
        }
    }

    #[test]
    fn test_runtime_config_files() {
        let tmp_dir = TestDir::new();
        let path = |name: &str| tmp_dir.path().join(name);
        fs::create_dir(path("usr.d")).unwrap();
        fs::create_dir(path("etc.d")).unwrap();
        for name in [
            "usr.yml", "usr.d/b.yml", "usr.d/a.yml", "usr.d/c.txt",
            "etc.yml", "etc.d/a.yml", "user.yml", "custom.yml"
        ] {
            fs::write(path(name), "").unwrap();
        }
        assert_eq!(
            runtime_config_files(
                &path("usr.yml"), &path("usr.d"),
                &path("etc.yml"), &path("etc.d"),
                Some(&path("user.yml")), Some(&path("custom.yml"))
            ).unwrap(),
            [
                "usr.yml", "usr.d/a.yml", "usr.d/b.yml", "etc.yml",
                "etc.d/a.yml", "user.yml", "custom.yml"
            ].map(path)
        );
        // missing files are skipped, except the custom file
        assert_eq!(
            runtime_config_files(
                &path("none.yml"), &path("none.d"),
                &path("etc.yml"), &path("none.d"),
                Some(&path("none.yml")), None
            ).unwrap(),
            [path("etc.yml")]
        );
        assert!(
            runtime_config_files(
                &path("usr.yml"), &path("usr.d"),
                &path("etc.yml"), &path("etc.d"),
                None, Some(&path("none.yml"))
            ).is_err()
        );
    }

    #[test]
    fn test_get_runtime_settings_custom_config() {
        // The custom config takes precedence over the default
        // config files present on the host running the test
        let tmp_dir = TestDir::new();
        let config_file = tmp_dir.path().join("custom.yml");
        fs::write(
            &config_file,
            "boxbuild:\n  runtime_container: custom/box\n  \
            runtime_wsl_image: https://example.com/b.wsl\n"
        ).unwrap();
        assert_eq!(
            get_runtime_settings(config_file.to_str()).unwrap(),
            RuntimeSettings {
                container: "custom/box".to_string(),
                wsl_image: Some("https://example.com/b.wsl".to_string())
            }
        );
    }
}
