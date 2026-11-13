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
//! Run the boxbuild runtime as WSL2 distribution on Windows
//!
//! On Windows there is no podman to run the runtime container.
//! The runtime is provided as WSL2 image instead, which is
//! registered as the WSL2 distribution defaults::WSL_DISTRIBUTION.
//! kiwi-ng runs in this distribution and starts the box as a KVM
//! based virtual machine, which requires nested virtualization
//! in WSL2.
//!
//! The Windows drives are mounted in WSL2, such that the image
//! description and the target directory are passed to kiwi by
//! their location in WSL2 instead of being mounted. The boxes
//! are stored in the distribution itself.
use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

use crate::build::{boxbuild_args, global_args};
use crate::cli::{BoxbuildOptions, GlobalOptions};
use crate::defaults;

pub fn image_location(setting: Option<&str>, arch: &str) -> String {
    /*!
    Provide the location of the WSL2 image of the runtime: the
    runtime_wsl_image setting if given, otherwise the default
    image for the given architecture
    !*/
    match setting {
        Some(setting) => setting.to_string(),
        None => defaults::RUNTIME_WSL_IMAGE.replace("{arch}", arch)
    }
}

fn is_url(location: &str) -> bool {
    ["http://", "https://", "ftp://"].iter()
        .any(|scheme| location.starts_with(scheme))
}

pub fn wsl_path(path: &Path) -> Option<String> {
    /*!
    Provide the location of the given Windows path in WSL2

    WSL2 mounts the Windows drives below defaults::WSL_MOUNT_ROOT,
    e.g C:\Users\me is available as /mnt/c/Users/me. The path can
    be given in the extended form fs::canonicalize() provides,
    e.g \\?\C:\Users\me. Network shares are not mounted in WSL2
    and cannot be used
    !*/
    let name = path.to_string_lossy();
    let name = name.strip_prefix(r"\\?\").unwrap_or(&name);
    let mut chars = name.chars();
    match (chars.next(), chars.next()) {
        (Some(drive), Some(':')) if drive.is_ascii_alphabetic() => {
            let rest = name[2..].replace('\\', "/");
            let rest = rest.trim_end_matches('/');
            Some(format!(
                "{}/{}{}{}", defaults::WSL_MOUNT_ROOT,
                drive.to_ascii_lowercase(),
                if rest.starts_with('/') || rest.is_empty() { "" } else { "/" },
                rest
            ))
        },
        _ => {
            error!(
                "Path {name} is not located on a Windows drive, which is \
                required to access it from WSL2"
            );
            None
        }
    }
}

pub fn split_shared_path(spec: &str) -> (&str, Option<&str>) {
    /*!
    Split the shared path given as HOST_PATH or HOST_PATH:BOX_PATH

    The colon of the drive letter of a Windows path, e.g C:\data,
    does not separate a box path
    !*/
    let bytes = spec.as_bytes();
    let skip = if bytes.len() >= 2
        && bytes[0].is_ascii_alphabetic() && bytes[1] == b':'
    {
        2
    } else {
        0
    };
    match spec[skip..].find(':') {
        Some(index) => (&spec[..skip + index], Some(&spec[skip + index + 1..])),
        None => (spec, None)
    }
}

fn data_dir() -> Option<PathBuf> {
    /*!
    Provide the directory below %LOCALAPPDATA% which holds the
    downloaded image and the files of the distribution, and
    create it if needed
    !*/
    let local_app_data = match std::env::var("LOCALAPPDATA") {
        Ok(dir) if ! dir.is_empty() => PathBuf::from(dir),
        _ => match std::env::var("USERPROFILE") {
            Ok(dir) if ! dir.is_empty() => {
                Path::new(&dir).join("AppData").join("Local")
            },
            _ => {
                error!(
                    "Neither LOCALAPPDATA nor USERPROFILE is set, cannot \
                    locate the directory to store the runtime in"
                );
                return None
            }
        }
    };
    let data_dir = local_app_data.join(defaults::WSL_DATA_DIR_NAME);
    if let Err(error) = fs::create_dir_all(&data_dir) {
        error!("Failed to create {}: {error}", data_dir.display());
        return None
    }
    Some(data_dir)
}

pub fn prepare_runtime(image: &str) -> bool {
    /*!
    Make sure the runtime is registered as WSL2 distribution in
    the latest version of its image

    An image given by URL is downloaded if the server provides a
    newer one than the one downloaded before, in the same way as
    podman pulls a newer runtime container. A new image replaces
    the registered distribution, which also drops the boxes stored
    in it. An image given as file is registered as it is
    !*/
    let data_dir = match data_dir() {
        Some(data_dir) => data_dir,
        None => return false
    };
    let (image_file, updated) = if is_url(image) {
        let image_file = data_dir.join(defaults::WSL_IMAGE_NAME);
        match download_image(image, &image_file) {
            Some(updated) => (image_file, updated),
            None => return false
        }
    } else {
        let image_file = PathBuf::from(image);
        if ! image_file.is_file() {
            error!("WSL2 image {image} not found");
            return false
        }
        (image_file, false)
    };
    let registered = match is_registered() {
        Some(registered) => registered,
        None => return false
    };
    if registered && ! updated {
        return true
    }
    if registered {
        info!("Replacing WSL2 distribution {}...", defaults::WSL_DISTRIBUTION);
        if run(&mut unregister_call(), "Unregistering WSL2 distribution") != 0 {
            return false
        }
    } else {
        info!("Registering WSL2 distribution {}...", defaults::WSL_DISTRIBUTION);
    }
    let install_dir = data_dir.join(defaults::WSL_INSTALL_DIR_NAME);
    run(&mut install_call(&image_file, &install_dir), "Registering WSL2 distribution") == 0
}

fn download_image(url: &str, image_file: &Path) -> Option<bool> {
    /*!
    Download the image from the given URL if it is newer than the
    image downloaded before and tell if it was downloaded

    The image is downloaded to a temporary file first, such that
    an interrupted download does not leave a broken image behind.
    curl only writes the file if the server provides a newer image
    !*/
    let part_file = image_file.with_extension("wsl.part");
    let _ = fs::remove_file(&part_file);
    let mut call = download_call(url, image_file, &part_file);
    info!("Checking for WSL2 runtime image update at {url}...");
    if run(&mut call, "Download of the WSL2 runtime image") != 0 {
        let _ = fs::remove_file(&part_file);
        return None
    }
    if ! part_file.is_file() {
        debug!("WSL2 runtime image {} is up to date", image_file.display());
        return Some(false)
    }
    if let Err(error) = fs::rename(&part_file, image_file) {
        error!(
            "Failed to store the WSL2 runtime image {}: {error}",
            image_file.display()
        );
        return None
    }
    Some(true)
}

fn download_call(url: &str, image_file: &Path, part_file: &Path) -> Command {
    let mut call = Command::new(defaults::CURL_PATH);
    call.arg("--fail")
        .arg("--location")
        .arg("--progress-bar")
        .arg("--show-error")
        .arg("--remote-time")
        .arg("--output").arg(part_file);
    // Only download an image newer than the one downloaded before
    if image_file.is_file() {
        call.arg("--time-cond").arg(image_file);
    }
    call.arg(url);
    call
}

fn wsl() -> Command {
    /*!
    Provide a call of wsl.exe which writes its own messages in
    UTF-8 instead of UTF-16
    !*/
    let mut call = Command::new(defaults::WSL_PATH);
    call.env("WSL_UTF8", "1");
    call
}

fn is_registered() -> Option<bool> {
    let mut call = wsl();
    call.arg("--list").arg("--quiet")
        .stdin(Stdio::null())
        .stderr(Stdio::inherit());
    debug!("{call:?}");
    match call.output() {
        Ok(output) => Some(
            distribution_listed(&output.stdout, defaults::WSL_DISTRIBUTION)
        ),
        Err(error) => {
            error!(
                "Failed to execute {}: {error}. WSL2 is required to run \
                kiwi-boxbuild on Windows", defaults::WSL_PATH
            );
            None
        }
    }
}

pub fn distribution_listed(output: &[u8], name: &str) -> bool {
    /*!
    Tell if the output of 'wsl.exe --list --quiet' lists the given
    distribution. Older versions of wsl.exe ignore WSL_UTF8 and
    write UTF-16, which is recognized by its zero bytes
    !*/
    let text = if output.contains(&0) {
        let units: Vec<u16> = output.chunks_exact(2)
            .map(|pair| u16::from_le_bytes([pair[0], pair[1]]))
            .collect();
        String::from_utf16_lossy(&units)
    } else {
        String::from_utf8_lossy(output).into_owned()
    };
    text.lines()
        .map(|line| line.trim_matches(|c: char| c.is_whitespace() || c == '\u{feff}'))
        .any(|line| line.eq_ignore_ascii_case(name))
}

fn unregister_call() -> Command {
    let mut call = wsl();
    call.arg("--unregister").arg(defaults::WSL_DISTRIBUTION);
    call
}

fn install_call(image_file: &Path, install_dir: &Path) -> Command {
    let mut call = wsl();
    call.arg("--install")
        .arg("--from-file").arg(image_file)
        .arg("--name").arg(defaults::WSL_DISTRIBUTION)
        .arg("--location").arg(install_dir)
        .arg("--no-launch");
    call
}

fn exec(env: &[(&str, String)]) -> Command {
    /*!
    Provide the call which runs a command in the distribution as
    root, without a shell in between. Environment variables are
    set with env, wsl.exe does not pass them along
    !*/
    let mut call = wsl();
    call.arg("--distribution").arg(defaults::WSL_DISTRIBUTION)
        .arg("--user").arg("root")
        .arg("--exec");
    if ! env.is_empty() {
        call.arg("/usr/bin/env");
        for (variable, value) in env {
            call.arg(format!("{variable}={value}"));
        }
    }
    call
}

pub fn kvm_available() -> bool {
    /*!
    Check if KVM is available in the distribution, which requires
    nested virtualization in WSL2
    !*/
    let mut call = exec(&[]);
    call.arg("/usr/bin/test").arg("-c").arg("/dev/kvm");
    debug!("{call:?}");
    matches!(call.status(), Ok(status) if status.success())
}

fn boxes_config_env(boxes_config: Option<&Path>) -> Option<Vec<(&'static str, String)>> {
    match boxes_config {
        Some(boxes_config) => Some(vec![(
            defaults::KIWI_BOXES_CONFIG_ENV, wsl_path(boxes_config)?
        )]),
        None => Some(Vec::new())
    }
}

pub fn list_boxes_call(
    boxes_config: Option<&Path>, global: &GlobalOptions
) -> Option<Command> {
    let mut call = exec(&boxes_config_env(boxes_config)?);
    call.arg(defaults::KIWI_PATH)
        .args(global_args(global))
        .arg("system").arg("boxbuild")
        .arg("--list-boxes");
    Some(call)
}

pub fn boxbuild_call(
    description: &Path, target_dir: &Path, boxes_config: Option<&Path>,
    shared_path: Option<&Path>, global: &GlobalOptions,
    boxbuild: &BoxbuildOptions, build_options: &[String]
) -> Option<Command> {
    /*!
    Create the wsl.exe call which runs the kiwi boxbuild of the
    given description in the distribution. All paths are passed
    by their location in WSL2
    !*/
    let description = wsl_path(description)?;
    let target_dir = wsl_path(target_dir)?;
    let shared_path = match shared_path {
        Some(shared_path) => Some(PathBuf::from(wsl_path(shared_path)?)),
        None => None
    };
    let mut call = exec(&boxes_config_env(boxes_config)?);
    call.arg(defaults::KIWI_PATH)
        .args(global_args(global))
        .arg("system").arg("boxbuild")
        .args(boxbuild_args(boxbuild, shared_path.as_deref()))
        .arg("kiwi")
        .arg("--description").arg(description)
        .arg("--target-dir").arg(target_dir)
        .args(build_options);
    Some(call)
}

fn run(call: &mut Command, action: &str) -> i32 {
    debug!("{call:?}");
    match call.status() {
        Ok(status) if status.success() => 0,
        Ok(status) => {
            let code = status.code().unwrap_or(255);
            error!("{action} failed with exit code {code}");
            code
        },
        Err(error) => {
            error!(
                "Failed to execute {}: {error}",
                call.get_program().to_string_lossy()
            );
            255
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cli::{Cli, Commands};
    use crate::test_helper::TestDir;
    use clap::Parser;

    fn call_args(call: &Command) -> Vec<String> {
        call.get_args()
            .map(|arg| arg.to_string_lossy().to_string()).collect()
    }

    fn strings(args: &[&str]) -> Vec<String> {
        args.iter().map(|arg| arg.to_string()).collect()
    }

    #[test]
    fn test_image_location() {
        assert_eq!(
            image_location(None, "x86_64"),
            "https://download.opensuse.org/repositories/Virtualization:/\
            Appliances:/SelfContained:/runtime/images/\
            boxbuild.x86_64-WSL.wsl"
        );
        assert!(image_location(None, "aarch64").ends_with(
            "/boxbuild.aarch64-WSL.wsl"
        ));
        assert_eq!(
            image_location(Some(r"C:\images\boxbuild.wsl"), "x86_64"),
            r"C:\images\boxbuild.wsl"
        );
        assert!(is_url(&image_location(None, "x86_64")));
        assert!(! is_url(r"C:\images\boxbuild.wsl"));
    }

    #[test]
    fn test_wsl_path() {
        for (windows, wsl) in [
            (r"C:\Users\me\desc", "/mnt/c/Users/me/desc"),
            (r"\\?\D:\images\result\", "/mnt/d/images/result"),
            (r"c:\", "/mnt/c"),
            ("E:/data", "/mnt/e/data"),
        ] {
            assert_eq!(wsl_path(Path::new(windows)).as_deref(), Some(wsl));
        }
        for path in [r"\\server\share\desc", r"\\?\UNC\server\share", "/mnt/c"] {
            assert!(wsl_path(Path::new(path)).is_none(), "{path}");
        }
    }

    #[test]
    fn test_split_shared_path() {
        assert_eq!(split_shared_path(r"C:\data"), (r"C:\data", None));
        assert_eq!(
            split_shared_path(r"C:\data:/repos"), (r"C:\data", Some("/repos"))
        );
        assert_eq!(split_shared_path("/data:/repos"), ("/data", Some("/repos")));
        assert_eq!(split_shared_path("/data"), ("/data", None));
    }

    #[test]
    fn test_distribution_listed() {
        assert!(distribution_listed(b"Ubuntu\r\nkiwi-boxbuild\r\n", "kiwi-boxbuild"));
        assert!(! distribution_listed(b"Ubuntu\r\n", "kiwi-boxbuild"));
        // older wsl.exe versions write UTF-16 with a byte order mark
        let utf16: Vec<u8> = "\u{feff}Ubuntu\r\nKIWI-BOXBUILD\r\n"
            .encode_utf16().flat_map(|unit| unit.to_le_bytes()).collect();
        assert!(distribution_listed(&utf16, "kiwi-boxbuild"));
        assert!(! distribution_listed(b"", "kiwi-boxbuild"));
    }

    #[test]
    fn test_install_and_download_calls() {
        assert_eq!(
            call_args(&install_call(
                Path::new(r"C:\data\boxbuild.wsl"), Path::new(r"C:\data\distribution")
            )),
            strings(&[
                "--install", "--from-file", r"C:\data\boxbuild.wsl",
                "--name", "kiwi-boxbuild", "--location", r"C:\data\distribution",
                "--no-launch"
            ])
        );
        assert_eq!(
            call_args(&unregister_call()), ["--unregister", "kiwi-boxbuild"]
        );
        // without a former download there is no time condition
        let tmp_dir = TestDir::new();
        let image_file = tmp_dir.path().join("boxbuild.wsl");
        let part_file = tmp_dir.path().join("boxbuild.wsl.part");
        let args = call_args(&download_call("https://x/b.wsl", &image_file, &part_file));
        assert!(! args.contains(&"--time-cond".to_string()));
        assert!(args.ends_with(&strings(&[
            "--output", &part_file.to_string_lossy(), "https://x/b.wsl"
        ])));
        // with a former download only a newer image is downloaded
        fs::write(&image_file, "").unwrap();
        let args = call_args(&download_call("https://x/b.wsl", &image_file, &part_file));
        assert!(args.ends_with(&strings(&[
            "--time-cond", &image_file.to_string_lossy(), "https://x/b.wsl"
        ])));
    }

    fn parse(args: &[&str]) -> (GlobalOptions, BoxbuildOptions, Vec<String>) {
        let mut call = vec!["kiwi-boxbuild"];
        call.extend_from_slice(args);
        let cli = Cli::parse_from(call);
        let build_options = match cli.command {
            Some(Commands::Kiwi { build_options }) => build_options,
            None => Vec::new()
        };
        (cli.global, cli.boxbuild, build_options)
    }

    #[test]
    fn test_boxbuild_call() {
        let (global, boxbuild, _) = parse(&[
            "--profile", "Virtual", "--box", "leap", "kiwi"
        ]);
        let call = boxbuild_call(
            Path::new(r"\\?\C:\work\desc"), Path::new(r"\\?\C:\work\result"),
            None, Some(Path::new(r"C:\repos")), &global, &boxbuild,
            &strings(&["--signing-key", "key"])
        ).unwrap();
        assert_eq!(call.get_program(), defaults::WSL_PATH);
        assert_eq!(call_args(&call), strings(&[
            "--distribution", "kiwi-boxbuild", "--user", "root", "--exec",
            "/usr/bin/kiwi-ng", "--profile", "Virtual",
            "system", "boxbuild", "--box", "leap", "--shared-path", "/mnt/c/repos",
            "kiwi", "--description", "/mnt/c/work/desc",
            "--target-dir", "/mnt/c/work/result", "--signing-key", "key"
        ]));

        // a custom boxes configuration is passed by environment
        let call = boxbuild_call(
            Path::new(r"C:\desc"), Path::new(r"C:\result"),
            Some(Path::new(r"C:\boxes.yml")), None, &global, &boxbuild, &[]
        ).unwrap();
        assert!(call_args(&call).starts_with(&strings(&[
            "--distribution", "kiwi-boxbuild", "--user", "root", "--exec",
            "/usr/bin/env", "KIWI_BOXED_PLUGIN_CFG=/mnt/c/boxes.yml",
            "/usr/bin/kiwi-ng"
        ])));

        // paths which are not accessible from WSL2
        assert!(boxbuild_call(
            Path::new(r"\\server\share\desc"), Path::new(r"C:\result"),
            None, None, &global, &boxbuild, &[]
        ).is_none());
    }

    #[test]
    fn test_list_boxes_call() {
        let (global, _, _) = parse(&["--list-boxes", "--debug"]);
        let call = list_boxes_call(None, &global).unwrap();
        assert_eq!(call_args(&call), strings(&[
            "--distribution", "kiwi-boxbuild", "--user", "root", "--exec",
            "/usr/bin/kiwi-ng", "--debug", "system", "boxbuild", "--list-boxes"
        ]));
    }
}
