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
use std::fs;
use std::io::{self, IsTerminal};
use std::path::{Component, Path, PathBuf};
use std::process::{Command, ExitStatus, Stdio};

use crate::boxes;
use crate::cli::{BoxbuildOptions, GlobalOptions};
use crate::defaults;
use crate::wsl;

/// The environment the build runs in
#[derive(Debug, PartialEq)]
pub enum Runtime {
    /// The runtime container run with podman, on Linux
    Container(String),
    /// The runtime registered as WSL2 distribution from the given
    /// image URL or file, on Windows
    Wsl(String),
}

impl Runtime {
    pub fn for_host(container: &str, wsl_image: Option<&str>) -> Runtime {
        /*!
        Select the runtime for the operating system kiwi-boxbuild
        is built for: the WSL2 distribution on Windows, the
        runtime container on all other systems
        !*/
        Runtime::select(cfg!(windows), container, wsl_image)
    }

    pub fn select(
        windows: bool, container: &str, wsl_image: Option<&str>
    ) -> Runtime {
        if windows {
            Runtime::Wsl(wsl::image_location(wsl_image, boxes::host_arch()))
        } else {
            Runtime::Container(container.to_string())
        }
    }

    pub fn name(&self) -> &str {
        match self {
            Runtime::Container(container) => container,
            Runtime::Wsl(image) => image
        }
    }
}

/// Options of the kiwi-ng system build command to run in the box
#[derive(Debug, PartialEq)]
pub struct BuildOptions {
    /// Host path of the image description
    pub description: String,
    /// Host path of the target directory
    pub target_dir: String,
    /// All other options, passed along as they are
    pub options: Vec<String>,
}

/// Host directory to share with the box along with its
/// location in the box
#[derive(Debug, PartialEq)]
pub struct SharedPath {
    pub host: PathBuf,
    pub target: PathBuf,
}

pub fn build_image(
    global: &GlobalOptions, boxbuild: &BoxbuildOptions,
    build_options: &[String], boxbuild_config: Option<&str>,
    runtime: &Runtime
) -> i32 {
    /*!
    Build the image description passed along with the build
    options in a box

    The build runs 'kiwi-ng system boxbuild' in an instance of the
    runtime container, see boxbuild_call, or on Windows in the WSL2
    distribution of the runtime, see wsl::boxbuild_call. The result
    of the build and the build log is stored in the target directory
    !*/
    let result = 255;

    let build_options = match split_build_options(build_options) {
        Some(build_options) => build_options,
        None => return result
    };

    // Check the paths upfront, a build takes long and should not
    // fail at the end because the result cannot be stored
    let description = match real_dir(&build_options.description) {
        Some(description) => description,
        None => return result
    };
    if let Err(error) = fs::create_dir_all(&build_options.target_dir) {
        error!("Failed to create {}: {error}", build_options.target_dir);
        return result
    }
    let target_dir = match real_dir(&build_options.target_dir) {
        Some(target_dir) => target_dir,
        None => return result
    };
    let shared_path = match &boxbuild.shared_path {
        Some(shared_path) => match parse_shared_path(shared_path, runtime) {
            Some(shared_path) => Some(shared_path),
            None => return result
        },
        None => None
    };
    let boxes_config = match boxbuild_config {
        Some(boxbuild_config) => match real_file(boxbuild_config) {
            Some(boxes_config) => Some(boxes_config),
            None => return result
        },
        None => None
    };

    // The exit code of a former build in the same target
    // directory must not be taken for the one of this build
    let exit_code_file = target_dir.join(defaults::KIWI_RESULT_CODE_NAME);
    if let Err(error) = fs::remove_file(&exit_code_file) {
        if error.kind() != io::ErrorKind::NotFound {
            error!(
                "Failed to delete former exit code {}: {error}",
                exit_code_file.display()
            );
            return result
        }
    }

    let call = match runtime {
        Runtime::Container(container) => {
            let boxes_dir = match boxes_dir() {
                Some(boxes_dir) => boxes_dir,
                None => return result
            };
            let shm_size = if boxbuild.virtiofs_sharing {
                match shm_size(boxbuild.box_memory.as_deref()) {
                    Some(shm_size) => Some(shm_size),
                    None => return result
                }
            } else {
                None
            };
            boxbuild_call(
                &description, &target_dir, &boxes_dir,
                boxes_config.as_deref(), shared_path.as_ref(), shm_size,
                global, boxbuild, &build_options.options, container
            )
        },
        Runtime::Wsl(image) => {
            if ! wsl::prepare_runtime(image) {
                return result
            }
            if ! boxbuild.no_accel && ! wsl::kvm_available() {
                error!(
                    "KVM is not available in WSL2, which requires nested \
                    virtualization. Enable it for WSL2 with a kernel that \
                    supports it, or build without acceleration using \
                    --no-accel, which is very slow"
                );
                return result
            }
            wsl::boxbuild_call(
                &description, &target_dir, boxes_config.as_deref(),
                shared_path.as_ref().map(|shared_path| &*shared_path.host),
                global, boxbuild, &build_options.options
            )
        }
    };
    let mut build_result = match call {
        Some(mut call) => {
            info!(
                "Building in box {} using {}...",
                boxbuild.boxname.as_deref().unwrap_or_default(),
                runtime.name()
            );
            run_build(&mut call, "Build")
        },
        None => result
    };
    report_build_log(&target_dir);
    if build_result == 0 {
        if box_build_succeeded(&target_dir) {
            info!("Build result: {}", target_dir.display());
        } else {
            build_result = result
        }
    }
    build_result
}

pub fn list_boxes(
    global: &GlobalOptions, boxbuild_config: Option<&str>,
    runtime: &Runtime
) -> i32 {
    /*!
    Show the available boxes by 'kiwi-ng system boxbuild --list-boxes'
    in an instance of the runtime container, or on Windows in the
    WSL2 distribution of the runtime

    The boxes kiwi prints as yaml document are shown as table,
    see boxes::format_box_list(). Output which cannot be read as
    list of boxes is shown as it is
    !*/
    let boxes_config = match boxbuild_config {
        Some(boxbuild_config) => match real_file(boxbuild_config) {
            Some(boxes_config) => Some(boxes_config),
            None => return 255
        },
        None => None
    };
    let call = match runtime {
        Runtime::Container(container) => {
            let boxes_dir = match boxes_dir() {
                Some(boxes_dir) => boxes_dir,
                None => return 255
            };
            list_boxes_call(
                &boxes_dir, boxes_config.as_deref(), global, container
            )
        },
        Runtime::Wsl(image) => {
            if ! wsl::prepare_runtime(image) {
                return 255
            }
            wsl::list_boxes_call(boxes_config.as_deref(), global)
        }
    };
    let mut call = match call {
        Some(call) => call,
        None => return 255
    };
    let output = match run_output(&mut call, "Listing boxes") {
        Ok(output) => output,
        Err(exit_code) => return exit_code
    };
    debug!("Output of kiwi-ng system boxbuild --list-boxes:\n{output}");
    match boxes::parse_box_list(&output) {
        Ok(box_list) => {
            print!("{}", boxes::format_box_list(&box_list, boxes::host_arch()))
        },
        Err(error) => {
            warn!("Failed to read the list of boxes: {error}");
            warn!("Showing the output of kiwi as it is");
            print!("{output}")
        }
    }
    0
}

fn podman_run(
    boxes_dir: &Path, boxes_config: Option<&Path>, with_terminal: bool
) -> Option<Command> {
    /*!
    Create the podman call which runs an instance of the runtime
    container

    The runtime container runs privileged as the box is a KVM
    based virtual machine started from within the runtime
    container. The boxes are stored on the host, such that they
    are downloaded only once. A boxes configuration file given
    on the host is mounted read-only to the location kiwi reads
    the system wide boxes configuration from
    !*/
    let mut call = Command::new(defaults::PODMAN_PATH);
    call.arg("run")
        .arg("--rm")
        .arg("--privileged")
        .arg("--pull=newer");
    // The box console is passed through if there is a terminal,
    // e.g to work in the box kept open by --box-debug. A call whose
    // output is read gets no terminal, it would merge stderr into
    // stdout and change the line endings
    if with_terminal && io::stdin().is_terminal() {
        call.arg("--interactive").arg("--tty");
    }
    call.arg("--volume").arg(
        volume(boxes_dir, Path::new(defaults::KIWI_BOXES_DIR))?
    );
    if let Some(boxes_config) = boxes_config {
        call.arg("--volume").arg(format!(
            "{}:ro", volume(
                boxes_config, Path::new(defaults::KIWI_BOXES_CONFIG_FILE)
            )?
        ));
    }
    Some(call)
}

fn list_boxes_call(
    boxes_dir: &Path, boxes_config: Option<&Path>, global: &GlobalOptions,
    runtime_container: &str
) -> Option<Command> {
    let mut call = podman_run(boxes_dir, boxes_config, false)?;
    call.arg(runtime_container)
        .args(global_args(global))
        .arg("system").arg("boxbuild")
        .arg("--list-boxes");
    Some(call)
}

#[allow(clippy::too_many_arguments)]
fn boxbuild_call(
    description: &Path, target_dir: &Path, boxes_dir: &Path,
    boxes_config: Option<&Path>, shared_path: Option<&SharedPath>,
    shm_size: Option<u64>, global: &GlobalOptions,
    boxbuild: &BoxbuildOptions, build_options: &[String],
    runtime_container: &str
) -> Option<Command> {
    /*!
    Create the podman call which runs the kiwi boxbuild of the
    given description in the runtime container

    With the virtiofs sharing backend, kiwi backs the memory of
    the virtual machine by a file in /dev/shm, which is shared
    with virtiofsd. The size of /dev/shm in the runtime container
    is set to shm_size bytes, see shm_size()
    !*/
    let mut call = podman_run(boxes_dir, boxes_config, true)?;
    if let Some(shm_size) = shm_size {
        call.arg(format!("--shm-size={shm_size}b"));
    }
    call.arg("--volume").arg(
        volume(description, Path::new(defaults::KIWI_DESCRIPTION_DIR))?
    );
    call.arg("--volume").arg(
        volume(target_dir, Path::new(defaults::KIWI_TARGET_DIR))?
    );
    // kiwi shares the shared path from the runtime container into
    // the box at the same location. It is therefore mounted to the
    // location it is expected at in the box
    if let Some(shared_path) = shared_path {
        call.arg("--volume").arg(
            volume(&shared_path.host, &shared_path.target)?
        );
    }
    // The entry point of the runtime container is kiwi-ng
    call.arg(runtime_container)
        .args(global_args(global))
        .arg("system").arg("boxbuild")
        .args(boxbuild_args(
            boxbuild, shared_path.map(|shared_path| &*shared_path.target)
        ))
        .arg("kiwi")
        .arg("--description").arg(defaults::KIWI_DESCRIPTION_DIR)
        .arg("--target-dir").arg(defaults::KIWI_TARGET_DIR)
        .args(build_options);
    Some(call)
}

pub(crate) fn global_args(global: &GlobalOptions) -> Vec<String> {
    /*!
    Translate the global options into kiwi-ng global arguments,
    kiwi-ng system boxbuild passes them along to the build in
    the box
    !*/
    let mut args: Vec<String> = Vec::new();
    if global.debug {
        args.push("--debug".to_string());
    }
    for profile in &global.profile {
        args.push("--profile".to_string());
        args.push(profile.clone());
    }
    if let Some(image_type) = &global.image_type {
        args.push("--type".to_string());
        args.push(image_type.clone());
    }
    if let Some(kiwi_file) = &global.kiwi_file {
        args.push("--kiwi-file".to_string());
        args.push(kiwi_file.clone());
    }
    args
}

pub(crate) fn boxbuild_args(
    boxbuild: &BoxbuildOptions, shared_path: Option<&Path>
) -> Vec<String> {
    /*!
    Translate the boxbuild options into kiwi boxbuild arguments
    !*/
    let mut args: Vec<String> = Vec::new();
    let mut value = |option: &str, value: Option<String>| {
        if let Some(value) = value {
            args.push(option.to_string());
            args.push(value);
        }
    };
    value("--box", boxbuild.boxname.clone());
    value("--box-memory", boxbuild.box_memory.clone());
    value("--box-console", boxbuild.box_console.clone());
    value("--box-smp-cpus", boxbuild.box_smp_cpus.map(|n| n.to_string()));
    value("--kiwi-version", boxbuild.kiwi_version.clone());
    value("--kiwi-git", boxbuild.kiwi_git.clone());
    value("--shared-path", shared_path.map(|p| p.display().to_string()));
    value("--machine", boxbuild.machine.clone());
    value("--cpu", boxbuild.cpu.clone());
    for (option, set) in [
        ("--box-debug", boxbuild.box_debug),
        ("--no-update-check", boxbuild.no_update_check),
        ("--no-snapshot", boxbuild.no_snapshot),
        ("--no-accel", boxbuild.no_accel),
        ("--virtiofs-sharing", boxbuild.virtiofs_sharing),
    ] {
        if set {
            args.push(option.to_string());
        }
    }
    args
}

fn split_build_options(build_options: &[String]) -> Option<BuildOptions> {
    /*!
    Split the build options into the image description, the
    target directory and all other options

    The image description and the target directory are mounted
    into the runtime container and passed to the build by their
    location in the runtime container instead. Both options are
    accepted as '--option value' and '--option=value'
    !*/
    let mut description = None;
    let mut target_dir = None;
    let mut options = Vec::new();
    let mut build_options = build_options.iter();
    while let Some(arg) = build_options.next() {
        let (option, value) = match arg.split_once('=') {
            Some((option, value)) => (option, Some(value.to_string())),
            None => (arg.as_str(), None)
        };
        if option != "--description" && option != "--target-dir" {
            options.push(arg.clone());
            continue
        }
        let value = match value.or_else(|| build_options.next().cloned()) {
            Some(value) => value,
            None => {
                error!("Option {option} requires a value");
                return None
            }
        };
        if option == "--description" {
            description = Some(value);
        } else {
            target_dir = Some(value);
        }
    }
    match (description, target_dir) {
        (Some(description), Some(target_dir)) => Some(
            BuildOptions { description, target_dir, options }
        ),
        (description, _) => {
            error!(
                "Required option missing in kiwi build command: {}",
                if description.is_none() {
                    "--description"
                } else {
                    "--target-dir"
                }
            );
            None
        }
    }
}

fn parse_shared_path(spec: &str, runtime: &Runtime) -> Option<SharedPath> {
    /*!
    Provide the shared path given as HOST_PATH or HOST_PATH:BOX_PATH

    Without BOX_PATH the host directory is shared at the same
    location in the box as on the host. BOX_PATH has to be an
    absolute path. It must not interfere with the locations used
    for the build in the runtime container, see boxbuild_call. The
    same applies to the location of the host directory if it is
    shared at the same location

    In the WSL2 distribution on Windows, the host directory is
    shared at its location in WSL2, e.g C:\data at /mnt/c/data,
    see wsl::boxbuild_call. A BOX_PATH is not supported there
    !*/
    let (host, target) = match runtime {
        Runtime::Wsl(_) => wsl::split_shared_path(spec),
        Runtime::Container(_) => match spec.split_once(':') {
            Some((host, target)) => (host, Some(target)),
            None => (spec, None)
        }
    };
    let host = real_dir(host)?;
    if let Runtime::Wsl(_) = runtime {
        if let Some(target) = target {
            error!(
                "Box path '{target}' of shared path {spec} is not \
                supported on Windows, the host path is shared at its \
                location in WSL2"
            );
            return None
        }
        return Some(SharedPath { target: host.clone(), host })
    }
    let target = match target {
        Some(target) => {
            let target = Path::new(target);
            let normal = target.components().all(|component| {
                matches!(component, Component::RootDir | Component::Normal(_))
            });
            if ! target.is_absolute() || ! normal {
                error!(
                    "Invalid box path '{}' in shared path {spec}: expected \
                    an absolute path without '.' and '..'",
                    target.display()
                );
                return None
            }
            target.to_path_buf()
        },
        None => host.clone()
    };
    for reserved in [
        defaults::KIWI_DESCRIPTION_DIR,
        defaults::KIWI_TARGET_DIR,
        defaults::KIWI_BOXES_DIR
    ] {
        let reserved = Path::new(reserved);
        if target.starts_with(reserved) || reserved.starts_with(&target) {
            error!(
                "Box path '{}' of shared path {spec} interferes with \
                {} used by the build",
                target.display(), reserved.display()
            );
            return None
        }
    }
    Some(SharedPath { host, target })
}

fn boxes_dir() -> Option<PathBuf> {
    /*!
    Provide the directory to store the boxes in on the host and
    create it if needed

    This is the same directory as used by kiwi-ng system boxbuild,
    $KIWI_BOXED_CACHE_DIR if it is set to an existing directory,
    otherwise $HOME/.kiwi_boxes
    !*/
    let boxes_dir = match std::env::var(defaults::KIWI_BOXES_DIR_ENV) {
        Ok(cache_dir) if Path::new(&cache_dir).is_dir() => {
            PathBuf::from(cache_dir)
        },
        _ => match std::env::var("HOME") {
            Ok(home) if ! home.is_empty() => {
                Path::new(&home).join(defaults::KIWI_BOXES_NAME)
            },
            _ => {
                error!(
                    "HOME is not set, cannot locate the boxes directory, \
                    set {} instead", defaults::KIWI_BOXES_DIR_ENV
                );
                return None
            }
        }
    };
    if let Err(error) = fs::create_dir_all(&boxes_dir) {
        error!("Failed to create {}: {error}", boxes_dir.display());
        return None
    }
    real_dir(&boxes_dir.to_string_lossy())
}

fn shm_size(box_memory: Option<&str>) -> Option<u64> {
    /*!
    Provide the size in bytes of /dev/shm in the runtime container
    to hold the memory of the virtual machine for the virtiofs
    sharing backend

    The size of /dev/shm is a limit, no memory is reserved by it.
    The memory of the virtual machine is given by --box-memory or
    otherwise by the configuration of the box, which is not known
    here. The size is therefore set to the memory the host can
    provide at all, its RAM and swap space, or to the given box
    memory if that is larger. This way the file backing the memory
    of the virtual machine always fits into /dev/shm
    !*/
    let box_memory = match box_memory {
        Some(box_memory) => match qemu_memory_size(box_memory) {
            Some(size) => Some(size),
            None => {
                error!(
                    "Invalid box memory '{box_memory}': expected a size \
                    as accepted by QEMU, e.g 4G or 4096"
                );
                return None
            }
        },
        None => None
    };
    let host_memory = fs::read_to_string("/proc/meminfo").ok()
        .and_then(|meminfo| host_memory_size(&meminfo));
    match (host_memory, box_memory) {
        (Some(host_memory), box_memory) => {
            Some(host_memory.max(box_memory.unwrap_or_default()))
        },
        (None, Some(box_memory)) => Some(box_memory),
        (None, None) => {
            error!(
                "Failed to read the host memory from /proc/meminfo, \
                use --box-memory to size /dev/shm for virtiofs sharing"
            );
            None
        }
    }
}

fn host_memory_size(meminfo: &str) -> Option<u64> {
    /*!
    Provide the RAM plus swap space in bytes from the given
    content of /proc/meminfo
    !*/
    let value = |key: &str| -> Option<u64> {
        meminfo.lines()
            .find_map(|line| line.strip_prefix(key))
            .and_then(|value| value.trim().strip_suffix("kB"))
            .and_then(|kib| kib.trim().parse::<u64>().ok())
            .map(|kib| kib * 1024)
    };
    Some(value("MemTotal:")? + value("SwapTotal:").unwrap_or_default())
}

fn qemu_memory_size(size: &str) -> Option<u64> {
    /*!
    Provide the given memory size in bytes as QEMU interprets it
    for the -m option: a number with an optional suffix of B, K, M,
    G or T. Without a suffix the number is taken as MiB
    !*/
    let size = size.trim();
    let (number, unit) = match size.char_indices().last() {
        Some((index, suffix)) if suffix.is_ascii_alphabetic() => {
            (&size[..index], suffix.to_ascii_uppercase())
        },
        _ => (size, 'M')
    };
    let factor: u64 = match unit {
        'B' => 1,
        'K' => 1 << 10,
        'M' => 1 << 20,
        'G' => 1 << 30,
        'T' => 1 << 40,
        _ => return None
    };
    let number: f64 = number.parse().ok()?;
    if ! number.is_finite() || number <= 0.0 {
        return None
    }
    Some((number * factor as f64).ceil() as u64)
}

fn run_build(call: &mut Command, action: &str) -> i32 {
    /*!
    Run the given call of the runtime container and provide
    its exit code, action names the call in error messages
    !*/
    debug!("{call:?}");
    match call.status() {
        Ok(status) => exit_code(status, action),
        Err(error) => {
            error!(
                "Failed to execute {}: {error}",
                call.get_program().to_string_lossy()
            );
            255
        }
    }
}

fn run_output(call: &mut Command, action: &str) -> Result<String, i32> {
    /*!
    Run the given call of the runtime container and provide its
    standard output, or its exit code if it failed

    The standard error is not read, messages of podman, e.g the
    progress of pulling the runtime container, and errors of kiwi
    are shown as they come. The output of a failed call is shown
    as well, it holds the log messages of kiwi
    !*/
    debug!("{call:?}");
    call.stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::inherit());
    match call.output() {
        Ok(output) => {
            let stdout = String::from_utf8_lossy(&output.stdout).into_owned();
            match exit_code(output.status, action) {
                0 => Ok(stdout),
                code => {
                    print!("{stdout}");
                    Err(code)
                }
            }
        },
        Err(error) => {
            error!(
                "Failed to execute {}: {error}",
                call.get_program().to_string_lossy()
            );
            Err(255)
        }
    }
}

fn exit_code(status: ExitStatus, action: &str) -> i32 {
    /*!
    Provide the exit code of the given status of a finished call,
    action names the call in error messages
    !*/
    match status.code() {
        Some(0) => 0,
        Some(code) => {
            error!("{action} failed with exit code {code}");
            code
        },
        None => {
            error!("{action} terminated by signal");
            255
        }
    }
}

fn box_build_succeeded(target_dir: &Path) -> bool {
    /*!
    Check the exit code of the build in the box

    The box stores it in the target directory. kiwi boxbuild does
    not fail if the box did not store an exit code at all, e.g if
    the box could not be started. Such a build is a failure too
    !*/
    let exit_code_file = target_dir.join(defaults::KIWI_RESULT_CODE_NAME);
    match fs::read_to_string(&exit_code_file) {
        Ok(exit_code) if exit_code.trim() == "0" => true,
        Ok(exit_code) => {
            error!("Box build failed with exit code {}", exit_code.trim());
            false
        },
        Err(error) => {
            error!(
                "Box build stored no exit code in {}: {error}",
                exit_code_file.display()
            );
            false
        }
    }
}

fn report_build_log(target_dir: &Path) {
    /*!
    Report the log the box has stored in the target directory,
    in particular to look into a failed build
    !*/
    let build_log = target_dir.join(defaults::KIWI_RESULT_LOG_NAME);
    if build_log.exists() {
        info!("Build log: {}", build_log.display());
    } else {
        warn!("Box build stored no log");
    }
}

fn real_dir(path: &str) -> Option<PathBuf> {
    /*!
    Provide the real path of the given directory
    !*/
    match fs::canonicalize(path) {
        Ok(real_path) if real_path.is_dir() => Some(real_path),
        Ok(_) => {
            error!("{path} is not a directory");
            None
        },
        Err(error) => {
            error!("Failed to access {path}: {error}");
            None
        }
    }
}

fn real_file(path: &str) -> Option<PathBuf> {
    /*!
    Provide the real path of the given file
    !*/
    match fs::canonicalize(path) {
        Ok(real_path) if real_path.is_file() => Some(real_path),
        Ok(_) => {
            error!("{path} is not a file");
            None
        },
        Err(error) => {
            error!("Failed to access {path}: {error}");
            None
        }
    }
}

fn volume(source: &Path, target: &Path) -> Option<String> {
    /*!
    Provide the podman volume specification which mounts the
    host path source to target in the container

    The ':' separates the fields of the specification and can
    therefore not be part of a path
    !*/
    let source = source.to_string_lossy();
    let target = target.to_string_lossy();
    if source.contains(':') || target.contains(':') {
        error!("Path {source} must not contain ':' to be mounted");
        return None
    }
    Some(format!("{source}:{target}"))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cli::{Cli, Commands};
    use crate::test_helper::TestDir;
    use clap::Parser;

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

    fn strings(args: &[&str]) -> Vec<String> {
        args.iter().map(|arg| arg.to_string()).collect()
    }

    fn call_args(call: &Command) -> Vec<String> {
        call.get_args()
            .map(|arg| arg.to_string_lossy().to_string()).collect()
    }

    #[test]
    fn test_global_args() {
        let (global, _, _) = parse(&["--box", "leap"]);
        assert!(global_args(&global).is_empty());
        let (global, _, _) = parse(&[
            "--profile", "a", "--box", "leap", "--profile", "b",
            "--type", "oem", "--kiwi-file", "my.kiwi", "--debug"
        ]);
        assert_eq!(global_args(&global), [
            "--debug", "--profile", "a", "--profile", "b",
            "--type", "oem", "--kiwi-file", "my.kiwi"
        ]);
    }

    #[test]
    fn test_boxbuild_args() {
        let (_, boxbuild, _) = parse(&["--box", "leap"]);
        assert_eq!(boxbuild_args(&boxbuild, None), ["--box", "leap"]);
        let (_, boxbuild, _) = parse(&[
            "--box", "universal", "--box-memory", "16", "--box-smp-cpus", "8",
            "--box-debug", "--no-snapshot", "--no-accel", "--no-update-check",
            "--box-console", "ttyS0", "--kiwi-version", "10.0.0",
            "--machine", "virt", "--cpu", "max", "--shared-path", "/var/tmp",
            "--virtiofs-sharing"
        ]);
        assert_eq!(boxbuild_args(&boxbuild, Some(Path::new("/var/tmp"))), [
            "--box", "universal", "--box-memory", "16",
            "--box-console", "ttyS0", "--box-smp-cpus", "8",
            "--kiwi-version", "10.0.0", "--shared-path", "/var/tmp",
            "--machine", "virt", "--cpu", "max",
            "--box-debug", "--no-update-check", "--no-snapshot", "--no-accel",
            "--virtiofs-sharing"
        ]);
        let (_, boxbuild, _) = parse(&[
            "--box", "leap",
            "--kiwi-git", "https://github.com/OSInside/kiwi/tree/main"
        ]);
        assert_eq!(boxbuild_args(&boxbuild, None), [
            "--box", "leap",
            "--kiwi-git", "https://github.com/OSInside/kiwi/tree/main"
        ]);
    }

    #[test]
    fn test_boxbuild_call() {
        let (global, boxbuild, build_options) = parse(&[
            "--profile", "Virtual", "--box", "leap", "kiwi",
            "--description", "desc", "--target-dir", "target",
            "--signing-key", "key"
        ]);
        let build_options = split_build_options(&build_options).unwrap();
        let shared_path = SharedPath {
            host: PathBuf::from("/host/shared"),
            target: PathBuf::from("/shared")
        };
        let call = boxbuild_call(
            Path::new("/desc"), Path::new("/target"), Path::new("/boxes"),
            None, Some(&shared_path), None, &global, &boxbuild,
            &build_options.options, "registry.example.com/box"
        ).unwrap();
        let args = call_args(&call);
        assert_eq!(call.get_program(), defaults::PODMAN_PATH);
        assert!(args.starts_with(&strings(&[
            "run", "--rm", "--privileged", "--pull=newer"
        ])));
        for volume in [
            "/boxes:/root/.kiwi_boxes", "/desc:/description",
            "/target:/result", "/host/shared:/shared"
        ] {
            assert!(args.contains(&volume.to_string()), "{}", volume);
        }
        assert!(args.ends_with(&strings(&[
            "registry.example.com/box", "--profile", "Virtual",
            "system", "boxbuild", "--box", "leap", "--shared-path", "/shared",
            "kiwi", "--description", "/description", "--target-dir", "/result",
            "--signing-key", "key"
        ])));

        // a path which cannot be expressed as podman volume
        assert!(boxbuild_call(
            Path::new("/de:sc"), Path::new("/target"), Path::new("/boxes"),
            None, None, None, &global, &boxbuild, &[], "registry.example.com/box"
        ).is_none());

        // /dev/shm is sized for the virtiofs sharing backend
        assert!(! args.iter().any(|arg| arg.starts_with("--shm-size")));
        let (global, boxbuild, _) = parse(&[
            "--box", "leap", "--virtiofs-sharing", "kiwi"
        ]);
        let call = boxbuild_call(
            Path::new("/desc"), Path::new("/target"), Path::new("/boxes"),
            None, None, Some(8589934592), &global, &boxbuild, &[],
            "registry.example.com/box"
        ).unwrap();
        let args = call_args(&call);
        assert!(args.contains(&"--shm-size=8589934592b".to_string()));
        assert!(args.ends_with(&strings(&[
            "registry.example.com/box", "system", "boxbuild", "--box", "leap",
            "--virtiofs-sharing", "kiwi", "--description", "/description",
            "--target-dir", "/result"
        ])));
    }

    #[test]
    fn test_list_boxes_call() {
        let (global, _, _) = parse(&["--list-boxes", "--debug"]);
        let call = list_boxes_call(
            Path::new("/boxes"), None, &global, "registry.example.com/box"
        ).unwrap();
        let args = call_args(&call);
        assert!(args.contains(&"/boxes:/root/.kiwi_boxes".to_string()));
        assert!(args.ends_with(&strings(&[
            "registry.example.com/box", "--debug",
            "system", "boxbuild", "--list-boxes"
        ])));
        // the output is read, the call gets no terminal
        assert!(! args.contains(&"--tty".to_string()));
        assert!(! args.contains(&"--interactive".to_string()));
    }

    #[test]
    fn test_boxes_config_volume() {
        let boxes_config_volume =
            "/host/boxes.yml:/etc/kiwi_boxed_plugin.yml:ro".to_string();
        let (global, boxbuild, _) = parse(&["--box", "leap", "kiwi"]);

        // no boxes config is shared by default
        let call = boxbuild_call(
            Path::new("/desc"), Path::new("/target"), Path::new("/boxes"),
            None, None, None, &global, &boxbuild, &[],
            "registry.example.com/box"
        ).unwrap();
        assert!(! call_args(&call).iter().any(
            |arg| arg.contains(defaults::KIWI_BOXES_CONFIG_FILE)
        ));

        // the boxes config is shared read-only for the build
        let call = boxbuild_call(
            Path::new("/desc"), Path::new("/target"), Path::new("/boxes"),
            Some(Path::new("/host/boxes.yml")), None, None, &global,
            &boxbuild, &[], "registry.example.com/box"
        ).unwrap();
        let args = call_args(&call);
        let index = args.iter().position(
            |arg| arg == &boxes_config_volume
        ).unwrap();
        assert_eq!(args[index - 1], "--volume");

        // and for listing the boxes, which are read from it
        let call = list_boxes_call(
            Path::new("/boxes"), Some(Path::new("/host/boxes.yml")),
            &global, "registry.example.com/box"
        ).unwrap();
        assert!(call_args(&call).contains(&boxes_config_volume));

        // a path which cannot be expressed as podman volume
        assert!(list_boxes_call(
            Path::new("/boxes"), Some(Path::new("/host/bo:xes.yml")),
            &global, "registry.example.com/box"
        ).is_none());
    }

    #[test]
    fn test_qemu_memory_size() {
        for (size, expected) in [
            ("4096", 4 << 30), ("4G", 4 << 30), ("4g", 4 << 30),
            ("8096M", 8096 << 20), ("1.5G", 3 << 29), ("1T", 1 << 40),
            ("512K", 512 << 10), ("1024B", 1024),
        ] {
            assert_eq!(qemu_memory_size(size), Some(expected), "{size}");
        }
        for size in ["", "G", "4X", "abc", "-1G", "0", "inf", "NaN"] {
            assert_eq!(qemu_memory_size(size), None, "{size}");
        }
    }

    #[test]
    fn test_host_memory_size() {
        let meminfo = "MemTotal:        3963532 kB\n\
            MemFree:          512000 kB\n\
            SwapTotal:       2097148 kB\n";
        assert_eq!(
            host_memory_size(meminfo), Some((3963532 + 2097148) * 1024)
        );
        // without swap
        assert_eq!(
            host_memory_size("MemTotal: 1024 kB\n"), Some(1024 * 1024)
        );
        assert_eq!(host_memory_size("SwapTotal: 1024 kB\n"), None);
    }

    #[test]
    fn test_shm_size() {
        // at least the memory of the host, at least the box memory
        let host_memory = host_memory_size(
            &fs::read_to_string("/proc/meminfo").unwrap()
        ).unwrap();
        assert_eq!(shm_size(None), Some(host_memory));
        assert_eq!(shm_size(Some("1M")), Some(host_memory));
        assert_eq!(shm_size(Some("1024T")), Some(1 << 50));
        assert_eq!(shm_size(Some("4X")), None);
    }

    #[test]
    fn test_split_build_options() {
        assert_eq!(
            split_build_options(&strings(&[
                "--description", "desc", "--allow-existing-root",
                "--target-dir=target", "--add-package", "vim"
            ])),
            Some(BuildOptions {
                description: "desc".to_string(),
                target_dir: "target".to_string(),
                options: strings(&[
                    "--allow-existing-root", "--add-package", "vim"
                ])
            })
        );
        for build_options in [
            &[][..],
            &["--description", "desc"][..],
            &["--target-dir", "target"][..],
            &["--target-dir", "target", "--description"][..],
        ] {
            assert!(
                split_build_options(&strings(build_options)).is_none(),
                "{:?}", build_options
            );
        }
    }

    #[test]
    fn test_parse_shared_path() {
        let container = Runtime::Container("box".to_string());
        let tmp_dir = TestDir::new();
        let host = fs::canonicalize(tmp_dir.path()).unwrap();
        let host_name = host.to_string_lossy().to_string();

        // shared at the same location as on the host
        assert_eq!(parse_shared_path(&host_name, &container), Some(SharedPath {
            host: host.clone(), target: host.clone()
        }));

        // shared at the given location in the box
        assert_eq!(
            parse_shared_path(&format!("{host_name}:/repos"), &container),
            Some(SharedPath {
                host: host.clone(), target: PathBuf::from("/repos")
            })
        );

        // the host path has to be an existing directory
        assert!(parse_shared_path("/nonexistent:/repos", &container).is_none());

        // the box path has to be absolute and normalized and must
        // not interfere with the locations used by the build
        for target in [
            "", "relative", "/a/../b", "/", "/description",
            "/result/sub", "/root", "/root/.kiwi_boxes"
        ] {
            assert!(
                parse_shared_path(&format!("{host_name}:{target}"), &container).is_none(),
                "{}", target
            );
        }
    }

    #[test]
    fn test_parse_shared_path_wsl() {
        // in WSL2 the host path is shared at its location there,
        // a box path is not supported
        let wsl = Runtime::Wsl("boxbuild.wsl".to_string());
        let tmp_dir = TestDir::new();
        let host = fs::canonicalize(tmp_dir.path()).unwrap();
        let host_name = host.to_string_lossy().to_string();
        assert_eq!(parse_shared_path(&host_name, &wsl), Some(SharedPath {
            host: host.clone(), target: host.clone()
        }));
        assert!(
            parse_shared_path(&format!("{host_name}:/repos"), &wsl).is_none()
        );
    }

    #[test]
    fn test_runtime_select() {
        assert_eq!(
            Runtime::select(false, "registry.example.com/box", None),
            Runtime::Container("registry.example.com/box".to_string())
        );
        assert_eq!(
            Runtime::select(true, "registry.example.com/box", None),
            Runtime::Wsl(wsl::image_location(None, boxes::host_arch()))
        );
        assert_eq!(
            Runtime::select(true, "box", Some("https://example.com/b.wsl")),
            Runtime::Wsl("https://example.com/b.wsl".to_string())
        );
        assert_eq!(
            Runtime::select(true, "box", Some("https://example.com/b.wsl"))
                .name(),
            "https://example.com/b.wsl"
        );
        // Linux builds use the runtime container
        assert_eq!(
            Runtime::for_host("box", None),
            Runtime::select(cfg!(windows), "box", None)
        );
    }

    #[test]
    fn test_box_build_succeeded() {
        let tmp_dir = TestDir::new();
        let exit_code_file = tmp_dir.path().join("result.code");
        assert!(! box_build_succeeded(tmp_dir.path()));
        fs::write(&exit_code_file, "1\n").unwrap();
        assert!(! box_build_succeeded(tmp_dir.path()));
        fs::write(&exit_code_file, "0\n").unwrap();
        assert!(box_build_succeeded(tmp_dir.path()));
    }

    #[test]
    fn test_real_dir() {
        let tmp_dir = TestDir::new();
        let file = tmp_dir.path().join("file");
        fs::write(&file, "").unwrap();
        assert_eq!(
            real_dir(&tmp_dir.path().to_string_lossy()),
            Some(fs::canonicalize(tmp_dir.path()).unwrap())
        );
        assert!(real_dir(&file.to_string_lossy()).is_none());
        assert!(real_dir("/nonexistent").is_none());
    }

    #[test]
    fn test_real_file() {
        let tmp_dir = TestDir::new();
        let file = tmp_dir.path().join("file");
        fs::write(&file, "").unwrap();
        assert_eq!(
            real_file(&file.to_string_lossy()),
            Some(fs::canonicalize(&file).unwrap())
        );
        assert!(real_file(&tmp_dir.path().to_string_lossy()).is_none());
        assert!(real_file("/nonexistent").is_none());
    }

    #[test]
    fn test_volume() {
        assert_eq!(
            volume(Path::new("/a"), Path::new("/b")).as_deref(), Some("/a:/b")
        );
        assert!(volume(Path::new("/a:b"), Path::new("/b")).is_none());
        assert!(volume(Path::new("/a"), Path::new("/b:c")).is_none());
    }
}
