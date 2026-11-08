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
#[macro_use]
extern crate log;

use clap::{CommandFactory, Parser};
use clap::error::ErrorKind;
use env_logger::Env;
use std::process::exit;

pub mod boxes;
pub mod build;
pub mod cli;
pub mod config;
pub mod defaults;

fn main() {
    let args = cli::translate_separator(std::env::args_os().collect());
    let cli = cli::Cli::parse_from(args);
    setup_logger(cli.global.debug);

    let runtime_container = match config::get_runtime_container(
        cli.config.as_deref()
    ) {
        Ok(runtime_container) => runtime_container,
        Err(error) => {
            error!("{error}");
            exit(1)
        }
    };

    let boxbuild_config = cli.boxbuild_config.as_deref();
    if cli.boxbuild.list_boxes {
        exit(
            build::list_boxes(
                &cli.global, boxbuild_config, &runtime_container
            )
        )
    }
    match &cli.command {
        Some(cli::Commands::Kiwi { build_options }) => {
            exit(
                build::build_image(
                    &cli.global, &cli.boxbuild, build_options,
                    boxbuild_config, &runtime_container
                )
            )
        },
        None => {
            cli::Cli::command().error(
                ErrorKind::MissingSubcommand,
                "The kiwi subcommand with the options of the kiwi build \
                command is required, e.g:\n\n  kiwi-boxbuild --box NAME kiwi \
                --description DIR --target-dir DIR"
            ).exit()
        }
    }
}

fn setup_logger(debug: bool) {
    let env = Env::default()
        .filter_or(
            "KIWI_BOXBUILD_LOG_LEVEL", if debug { "debug" } else { "info" }
        )
        .write_style_or("KIWI_BOXBUILD_LOG_STYLE", "never");
    env_logger::Builder::from_env(env)
        .format_timestamp(None)
        .format_target(false)
        .init();
}

#[cfg(test)]
mod test_helper {
    use std::fs;
    use std::path::{Path, PathBuf};
    use std::sync::atomic::{AtomicUsize, Ordering};

    static COUNTER: AtomicUsize = AtomicUsize::new(0);

    /// Temporary directory which is deleted when dropped
    pub struct TestDir(PathBuf);

    impl TestDir {
        pub fn new() -> TestDir {
            let path = std::env::temp_dir().join(format!(
                "kiwi-boxbuild-test-{}-{}",
                std::process::id(), COUNTER.fetch_add(1, Ordering::SeqCst)
            ));
            fs::create_dir_all(&path).unwrap();
            TestDir(path)
        }

        pub fn path(&self) -> &Path {
            &self.0
        }
    }

    impl Drop for TestDir {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.0);
        }
    }
}
