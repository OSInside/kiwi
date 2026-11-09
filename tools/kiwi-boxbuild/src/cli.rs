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
use clap::{Args, Parser, Subcommand};
use std::ffi::OsString;

/// Build an image in a self contained box
///
/// kiwi-boxbuild pulls the boxbuild runtime container and calls
/// the kiwi-ng system boxbuild command inside of it. The runtime
/// container provides kiwi and the requirements of the boxbuild
/// command, only podman is required on the host.
///
/// The runtime container is configured in the boxbuild section
/// of the kiwi runtime config, e.g /etc/kiwi.yml or
/// ~/.config/kiwi/config.yml:
///
/// boxbuild:
///   runtime_container: <container reference>
#[derive(Parser, Debug)]
#[clap(
    name = "kiwi-boxbuild",
    version,
    verbatim_doc_comment,
    disable_help_subcommand = true,
    subcommand_value_name = "kiwi",
    after_help = "\
Everything after the kiwi subcommand, or the '--' separator, is passed
along to the kiwi-ng system build command in the box. The options
--description and --target-dir are required:

  kiwi-boxbuild --profile Virtual --box leap kiwi \\
      --description DIR --target-dir DIR"
)]
pub struct Cli {
    #[clap(flatten)]
    pub global: GlobalOptions,

    #[clap(flatten)]
    pub boxbuild: BoxbuildOptions,

    /// Read the runtime container from the given kiwi runtime
    /// config file. The file takes precedence over the default
    /// runtime config files
    #[clap(long, value_name = "FILE", help_heading = "Options")]
    pub config: Option<String>,

    /// Use the given boxes configuration file instead of the
    /// one provided by the runtime container. The file is
    /// shared with the runtime container as
    /// /etc/kiwi_boxed_plugin.yml
    #[clap(long, value_name = "FILE", help_heading = "Options")]
    pub boxbuild_config: Option<String>,

    #[clap(subcommand)]
    pub command: Option<Commands>,
}

#[derive(Subcommand, Debug)]
pub enum Commands {
    /// Options of the kiwi-ng system build command to run in
    /// the box. The options --description and --target-dir
    /// are required
    Kiwi {
        #[clap(
            value_name = "BUILD_OPTIONS",
            trailing_var_arg = true,
            allow_hyphen_values = true
        )]
        build_options: Vec<String>,
    },
}

/// kiwi-ng global options passed along to the build in the box
#[derive(Args, Debug)]
#[clap(next_help_heading = "Global options")]
pub struct GlobalOptions {
    /// Profile to select from the image description, can be
    /// specified multiple times
    #[clap(long, value_name = "NAME")]
    pub profile: Vec<String>,

    /// Image build type to select from the image description
    #[clap(long = "type", value_name = "NAME")]
    pub image_type: Option<String>,

    /// Basename of the kiwi file to use from the image
    /// description, by default config.kiwi or config.xml
    #[clap(long, value_name = "NAME")]
    pub kiwi_file: Option<String>,

    /// Print debug information, this also applies to the
    /// build in the box
    #[clap(long)]
    pub debug: bool,
}

/// Options of the kiwi-ng system boxbuild command
///
/// Only the options which apply to a box started from within
/// the runtime container are provided. Not provided are the
/// build in a box container, as the runtime container does not
/// provide podman, the sshfs sharing backend, as the runtime
/// container does not provide sshfs and the box cannot connect
/// to the host through ssh, the selection of the default 9p
/// sharing backend, and the selection of a box for a foreign
/// architecture, as the runtime container only provides QEMU
/// for the host architecture
#[derive(Args, Debug)]
#[clap(next_help_heading = "Boxbuild options")]
pub struct BoxbuildOptions {
    /// Name of the box to use for the build process
    #[clap(
        long = "box", value_name = "NAME",
        required_unless_present = "list_boxes"
    )]
    pub boxname: Option<String>,

    /// Show available build boxes
    #[clap(long, conflicts_with = "boxname")]
    pub list_boxes: bool,

    /// Main memory to reserve for the virtual machine, passed
    /// to QEMU as it is. The value is taken as MiB unless a
    /// suffix is given, e.g 4G or 4096. By default the memory
    /// configured for the box is used, which is about 8G
    #[clap(long, value_name = "SIZE")]
    pub box_memory: Option<String>,

    /// Name of console in the kernel settings for the
    /// virtual machine. By default set to hvc0
    #[clap(long, value_name = "TTYNAME")]
    pub box_console: Option<String>,

    /// Number of CPUs to use in the SMP setup.
    /// By default 4 CPUs will be used
    #[clap(long, value_name = "NUMBER")]
    pub box_smp_cpus: Option<u32>,

    /// In debug mode the started virtual machine will
    /// be kept open
    #[clap(long)]
    pub box_debug: bool,

    /// Specify a KIWI version to use for the build. The
    /// referenced KIWI will be fetched from pip and replaces
    /// the box installed KIWI version. This option is
    /// mutually exclusive with --kiwi-git
    #[clap(long, value_name = "VERSION", conflicts_with = "kiwi_git")]
    pub kiwi_version: Option<String>,

    /// Specify a KIWI git link to use for the build, e.g
    /// https://github.com/OSInside/kiwi/tree/BRANCH_NAME.
    /// The referenced KIWI source will be cloned, built and
    /// installed in the box and replaces the box installed
    /// KIWI version. If no /tree/BRANCH_NAME is part of the
    /// link, the default branch of the repository is used.
    /// This option is mutually exclusive with --kiwi-version
    #[clap(long, value_name = "GIT_LINK")]
    pub kiwi_git: Option<String>,

    /// Optional host path to share with the box. The same
    /// path as it is present on the host will also be
    /// available inside of the box during build time.
    /// With HOST_PATH:BOX_PATH the host path is available
    /// at BOX_PATH inside of the box instead
    #[clap(long, value_name = "HOST_PATH[:BOX_PATH]")]
    pub shared_path: Option<String>,

    /// Skip check for available box update. The option has
    /// no effect if the selected box does not yet exist
    #[clap(long)]
    pub no_update_check: bool,

    /// Run box with snapshot mode switched off. This causes
    /// the box disk file to be modified by the build process
    /// and allows to keep a persistent package cache as part
    /// of the box
    #[clap(long)]
    pub no_snapshot: bool,

    /// Run box without hardware acceleration. By default
    /// KVM acceleration is activated
    #[clap(long)]
    pub no_accel: bool,

    /// Select virtiofsd backend to use for sharing data
    /// between the host and the box instead of 9p. The
    /// memory of the virtual machine is shared with virtiofsd
    /// through /dev/shm of the runtime container, which is
    /// sized such that it can hold the memory
    #[clap(long)]
    pub virtiofs_sharing: bool,

    /// Machine name used by QEMU. By default no specific
    /// value is used here and QEMU selects its default
    /// machine type. For system architectures for which
    /// QEMU defines no default like for Arm, it is required
    /// to specify a machine name, e.g virt
    #[clap(long, value_name = "QEMU_MACHINE")]
    pub machine: Option<String>,

    /// CPU type used by QEMU. By default the host CPU
    /// type is used
    #[clap(long, value_name = "QEMU_CPU")]
    pub cpu: Option<String>,
}

pub fn translate_separator(mut args: Vec<OsString>) -> Vec<OsString> {
    /*!
    Accept the '--' separator as an alias for the kiwi subcommand,
    in the same way as kiwi-ng system boxbuild does

    Only a separator in front of the kiwi subcommand is replaced,
    a '--' after it is passed along to the build in the box
    !*/
    for arg in args.iter_mut().skip(1) {
        if arg == "kiwi" {
            break
        }
        if arg == "--" {
            *arg = OsString::from("kiwi");
            break
        }
    }
    args
}

#[cfg(test)]
mod tests {
    use super::*;

    fn os_args(args: &[&str]) -> Vec<OsString> {
        args.iter().map(OsString::from).collect()
    }

    #[test]
    fn test_translate_separator() {
        assert_eq!(
            translate_separator(os_args(&[
                "kiwi-boxbuild", "--box", "leap", "--", "--description", "d"
            ])),
            os_args(&[
                "kiwi-boxbuild", "--box", "leap", "kiwi", "--description", "d"
            ])
        );
        // a separator after the kiwi subcommand is kept
        let args = os_args(&[
            "kiwi-boxbuild", "--box", "leap", "kiwi", "--description", "d",
            "--"
        ]);
        assert_eq!(translate_separator(args.clone()), args);
    }

    #[test]
    fn test_parse_build() {
        let cli = Cli::try_parse_from([
            "kiwi-boxbuild", "--profile", "a", "--box", "leap",
            "--profile", "b", "--type", "oem", "--debug",
            "--virtiofs-sharing", "kiwi",
            "--description", "d", "--target-dir", "t", "--signing-key", "k"
        ]).unwrap();
        assert_eq!(cli.global.profile, ["a", "b"]);
        assert_eq!(cli.global.image_type.as_deref(), Some("oem"));
        assert!(cli.global.debug);
        assert_eq!(cli.boxbuild.boxname.as_deref(), Some("leap"));
        assert!(cli.boxbuild.virtiofs_sharing);
        match cli.command {
            Some(Commands::Kiwi { build_options }) => assert_eq!(
                build_options, [
                    "--description", "d", "--target-dir", "t",
                    "--signing-key", "k"
                ]
            ),
            None => panic!("no kiwi subcommand")
        }
    }

    #[test]
    fn test_parse_list_boxes() {
        let cli = Cli::try_parse_from([
            "kiwi-boxbuild", "--list-boxes"
        ]).unwrap();
        assert!(cli.boxbuild.list_boxes);
        assert!(cli.command.is_none());
    }

    #[test]
    fn test_parse_boxbuild_config() {
        let cli = Cli::try_parse_from([
            "kiwi-boxbuild", "--list-boxes"
        ]).unwrap();
        assert!(cli.boxbuild_config.is_none());
        let cli = Cli::try_parse_from([
            "kiwi-boxbuild", "--boxbuild-config", "boxes.yml", "--list-boxes"
        ]).unwrap();
        assert_eq!(cli.boxbuild_config.as_deref(), Some("boxes.yml"));
    }

    #[test]
    fn test_parse_errors() {
        for args in [
            // a box is required
            &["kiwi-boxbuild", "kiwi", "--description", "d"][..],
            // listing the boxes does not select one
            &["kiwi-boxbuild", "--list-boxes", "--box", "leap"][..],
            // a kiwi version and a kiwi git link exclude each other
            &[
                "kiwi-boxbuild", "--box", "leap", "--kiwi-version", "10.0.0",
                "--kiwi-git", "https://github.com/OSInside/kiwi"
            ][..],
            // options which do not work in the runtime container
            // are not provided
            &["kiwi-boxbuild", "--box", "leap", "--container"][..],
            &["kiwi-boxbuild", "--box", "leap", "--sshfs-sharing"][..],
            &["kiwi-boxbuild", "--box", "leap", "--9p-sharing"][..],
            &["kiwi-boxbuild", "--box", "leap", "--ssh-key", "id"][..],
            &["kiwi-boxbuild", "--box", "leap", "--ssh-port", "22"][..],
            &["kiwi-boxbuild", "--box", "leap", "--x86_64"][..],
            &["kiwi-boxbuild", "--box", "leap", "--aarch64"][..],
        ] {
            assert!(Cli::try_parse_from(args).is_err(), "{:?}", args);
        }
    }

    fn completion_options(completion: &str, variable: &str) -> Vec<String> {
        // Options assigned to the given variable of the bash
        // completion as a quoted, whitespace separated list
        let start = completion.find(&format!("\n{variable}=\"")).unwrap()
            + variable.len() + 3;
        let end = start + completion[start..].find('"').unwrap();
        completion[start..end].split_whitespace().map(String::from).collect()
    }

    #[test]
    fn test_bash_completion() {
        // The options of the bash completion match the command
        // line interface, such that they do not get out of sync
        use clap::CommandFactory;
        let completion = include_str!("../completion/kiwi-boxbuild");
        let mut value_options = completion_options(
            completion, "_kiwi_boxbuild_value_options"
        );
        let mut flag_options = completion_options(
            completion, "_kiwi_boxbuild_flag_options"
        );
        let mut command = Cli::command();
        command.build();
        let mut cli_value_options = Vec::new();
        let mut cli_flag_options = Vec::new();
        for arg in command.get_arguments() {
            if let Some(long) = arg.get_long() {
                if arg.get_action().takes_values() {
                    cli_value_options.push(format!("--{long}"));
                } else {
                    cli_flag_options.push(format!("--{long}"));
                }
            }
        }
        for options in [
            &mut value_options, &mut flag_options,
            &mut cli_value_options, &mut cli_flag_options
        ] {
            options.sort();
        }
        assert_eq!(value_options, cli_value_options);
        assert_eq!(flag_options, cli_flag_options);
    }
}
