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

/// A box of the boxes configuration as listed by
/// kiwi-ng system boxbuild --list-boxes
///
/// Only the settings shown to the user are read, all other
/// settings of a box are ignored
#[derive(Debug, Deserialize, PartialEq)]
pub struct BoxInfo {
    pub name: String,
    #[serde(default)]
    pub mem_mb: Option<String>,
    #[serde(default)]
    pub processors: Option<serde_norway::Number>,
    #[serde(default)]
    pub console: Option<String>,
    #[serde(default)]
    pub arch: Vec<BoxArch>,
}

/// An architecture a box is provided for
#[derive(Debug, Deserialize, PartialEq)]
pub struct BoxArch {
    pub name: String,
}

// Levels of the kiwi log messages, see is_log_line()
const LOG_LEVELS: [&str; 5] = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"];

pub fn parse_box_list(output: &str) -> Result<Vec<BoxInfo>, String> {
    /*!
    Read the boxes from the output of kiwi-ng system boxbuild
    --list-boxes

    kiwi prints the box section of the boxes configuration as
    yaml document. Its log messages are written to the same
    output and are skipped, see is_log_line(). No boxes at all
    are printed as empty document
    !*/
    let yaml_data: String = output
        .lines()
        .filter(|line| ! is_log_line(line))
        .map(|line| format!("{line}\n"))
        .collect();
    if yaml_data.trim().is_empty() {
        return Ok(Vec::new())
    }
    serde_norway::from_str(&yaml_data).map_err(|error| error.to_string())
}

pub fn is_log_line(line: &str) -> bool {
    /*!
    Check if the given output line is a kiwi log message

    A log message is written as '[ LEVEL   ]: TIME | MESSAGE',
    optionally enclosed in terminal color sequences
    !*/
    let line = strip_color(line);
    let Some(rest) = line.strip_prefix('[') else {
        return false
    };
    match rest.split_once("]:") {
        Some((level, _)) => LOG_LEVELS.contains(&level.trim()),
        None => false
    }
}

fn strip_color(line: &str) -> &str {
    /*!
    Strip the terminal color sequences in front of the given line
    !*/
    let mut line = line;
    while let Some(rest) = line.strip_prefix("\x1b[") {
        match rest.find('m') {
            Some(end) => line = &rest[end + 1..],
            None => break
        }
    }
    line
}

pub fn format_box_list(boxes: &[BoxInfo], host_arch: &str) -> String {
    /*!
    Provide the given boxes as table for the console

    The box is built for the architecture of the host, as the
    runtime container only provides QEMU for it. Boxes which are
    not provided for the given host architecture are named below
    the table
    !*/
    if boxes.is_empty() {
        return "No boxes available\n".to_string()
    }
    let mut rows: Vec<[String; 5]> = vec![[
        "NAME".to_string(), "ARCHITECTURES".to_string(),
        "MEMORY".to_string(), "CPUS".to_string(), "CONSOLE".to_string()
    ]];
    for box_info in boxes {
        let architectures: Vec<&str> = box_info.arch.iter()
            .map(|arch| arch.name.as_str())
            .collect();
        rows.push([
            box_info.name.clone(),
            value_or_dash(Some(architectures.join(", "))),
            value_or_dash(box_info.mem_mb.clone()),
            value_or_dash(
                box_info.processors.as_ref().map(ToString::to_string)
            ),
            value_or_dash(box_info.console.clone())
        ]);
    }
    let mut widths = [0; 5];
    for row in &rows {
        for (width, value) in widths.iter_mut().zip(row) {
            *width = (*width).max(value.chars().count());
        }
    }
    let mut table = String::from(
        "Available boxes, select one with: kiwi-boxbuild --box NAME\n\n"
    );
    for row in &rows {
        let line: Vec<String> = row.iter().zip(widths)
            .map(|(value, width)| format!("{value:<width$}"))
            .collect();
        table.push_str(&format!("  {}\n", line.join("  ").trim_end()));
    }
    let unavailable: Vec<&str> = boxes.iter()
        .filter(|box_info| ! box_info.arch.iter().any(
            |arch| arch.name == host_arch
        ))
        .map(|box_info| box_info.name.as_str())
        .collect();
    if ! unavailable.is_empty() {
        table.push_str(&format!(
            "\nNot available for the host architecture {host_arch}: {}\n",
            unavailable.join(", ")
        ));
    }
    table
}

fn value_or_dash(value: Option<String>) -> String {
    /*!
    Provide the given value, a dash if it is not set or empty
    !*/
    match value {
        Some(value) if ! value.is_empty() => value,
        _ => "-".to_string()
    }
}

pub fn host_arch() -> &'static str {
    /*!
    Provide the architecture of the host in the notation of the
    boxes configuration
    !*/
    arch_name(std::env::consts::ARCH, cfg!(target_endian = "little"))
}

pub fn arch_name(rust_arch: &'static str, little_endian: bool) -> &'static str {
    /*!
    Translate the given Rust architecture name into the name
    used by the boxes configuration
    !*/
    match rust_arch {
        "powerpc64" if little_endian => "ppc64le",
        "powerpc64" => "ppc64",
        rust_arch => rust_arch
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // Output of kiwi-ng system boxbuild --list-boxes, shortened
    // to the settings of two boxes
    const LIST_BOXES_OUTPUT: &str = "\
[ INFO    ]: 10:26:55 | Reading boxes config file: /etc/kiwi_boxed_plugin.yml
- arch:
  - boxfiles:
    - TumbleWeed-Box.x86_64-Kernel.tar.xz
    - TumbleWeed-Box.x86_64-System.qcow2
    cmdline:
    - root=/dev/vda3
    - rd.plymouth=0
    container: registry.opensuse.org/tumbleweed:latest
    name: x86_64
    packages_file: TumbleWeed-Box.x86_64-System.json
    source: obs://Virtualization:Appliances:SelfContained:tumbleweed/images
    use_initrd: true
  - boxfiles:
    - TumbleWeed-Box.aarch64-Kernel.tar.xz
    - TumbleWeed-Box.aarch64-System.qcow2
    cmdline:
    - root=/dev/vda2
    container: registry.opensuse.org/tumbleweed:latest
    name: aarch64
    packages_file: TumbleWeed-Box.aarch64-System.json
    source: obs://Virtualization:Appliances:SelfContained:tumbleweed/images
    use_initrd: true
  console: hvc0
  mem_mb: 8096M
  name: tumbleweed
  processors: 4
- arch:
  - boxfiles:
    - Leap-Box.x86_64-Kernel.tar.xz
    cmdline:
    - root=/dev/vda1
    container: registry.opensuse.org/leap:latest
    name: x86_64
    packages_file: Leap-Box.x86_64-System.json
    source: obs://Virtualization:Appliances:SelfContained:leap/images
    use_initrd: true
  console: ttyS0
  mem_mb: 4096M
  name: leap

";

    fn box_info(
        name: &str, archs: &[&str], mem_mb: &str, processors: Option<u64>,
        console: &str
    ) -> BoxInfo {
        BoxInfo {
            name: name.to_string(),
            mem_mb: Some(mem_mb.to_string()),
            processors: processors.map(serde_norway::Number::from),
            console: Some(console.to_string()),
            arch: archs.iter()
                .map(|name| BoxArch { name: name.to_string() })
                .collect(),
        }
    }

    #[test]
    fn test_parse_box_list() {
        assert_eq!(
            parse_box_list(LIST_BOXES_OUTPUT).unwrap(),
            vec![
                box_info(
                    "tumbleweed", &["x86_64", "aarch64"], "8096M", Some(4),
                    "hvc0"
                ),
                box_info("leap", &["x86_64"], "4096M", None, "ttyS0"),
            ]
        );
        // debug and colored log messages are skipped as well
        let output = format!(
            "\x1b[1;30m[ DEBUG   ]: 10:26:55 | Using runtime config\x1b[0m\n\
            [ WARNING ]: 10:26:55 | Some warning\n{LIST_BOXES_OUTPUT}"
        );
        assert_eq!(parse_box_list(&output).unwrap().len(), 2);
    }

    #[test]
    fn test_parse_box_list_without_boxes() {
        // no boxes are printed as empty document
        assert_eq!(parse_box_list("").unwrap(), vec![]);
        assert_eq!(
            parse_box_list(
                "[ INFO    ]: 10:26:55 | Reading boxes config file: x\n\n"
            ).unwrap(),
            vec![]
        );
    }

    #[test]
    fn test_parse_box_list_invalid() {
        // output which is not a list of boxes is reported
        for output in [
            "Error: something went wrong\n",
            "- arch: []\n  console: hvc0\n",
            "box:\n  - name: leap\n",
        ] {
            assert!(parse_box_list(output).is_err(), "{output:?}");
        }
    }

    #[test]
    fn test_is_log_line() {
        for line in [
            "[ INFO    ]: 10:26:55 | Reading boxes config file: x",
            "[ DEBUG   ]: 10:26:55 | message",
            "[ WARNING ]: 10:26:55 | message",
            "[ ERROR   ]: 10:26:55 | message",
            "\x1b[1;30m[ DEBUG   ]: 10:26:55 | message\x1b[0m",
        ] {
            assert!(is_log_line(line), "{line:?}");
        }
        for line in [
            "- arch:",
            "  name: leap",
            "[ NOTE ]: not a kiwi log level",
            "[INFO",
            "",
        ] {
            assert!(! is_log_line(line), "{line:?}");
        }
    }

    #[test]
    fn test_format_box_list() {
        let boxes = vec![
            box_info(
                "tumbleweed", &["x86_64", "aarch64", "s390x"], "8096M",
                Some(4), "hvc0"
            ),
            box_info("leap", &["x86_64"], "4096M", None, "ttyS0"),
        ];
        assert_eq!(
            format_box_list(&boxes, "x86_64"),
            "\
Available boxes, select one with: kiwi-boxbuild --box NAME

  NAME        ARCHITECTURES           MEMORY  CPUS  CONSOLE
  tumbleweed  x86_64, aarch64, s390x  8096M   4     hvc0
  leap        x86_64                  4096M   -     ttyS0
"
        );
        // boxes which can't run on the host are named
        assert!(format_box_list(&boxes, "aarch64").ends_with(
            "\nNot available for the host architecture aarch64: leap\n"
        ));
        assert_eq!(format_box_list(&[], "x86_64"), "No boxes available\n");
    }

    #[test]
    fn test_arch_name() {
        assert_eq!(arch_name("x86_64", true), "x86_64");
        assert_eq!(arch_name("aarch64", true), "aarch64");
        assert_eq!(arch_name("s390x", false), "s390x");
        assert_eq!(arch_name("powerpc64", true), "ppc64le");
        assert_eq!(arch_name("powerpc64", false), "ppc64");
    }
}
