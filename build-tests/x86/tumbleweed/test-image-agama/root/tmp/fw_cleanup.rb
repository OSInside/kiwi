#! /usr/bin/env ruby

# This script removes unused firmware files (not referenced by any kernel
# driver) from the system. By default the script runs in safe mode and only
# lists the unused firmware file, use the "--delete" argument to delete the
# found files.

require "find"
require "shellwords"

fw_dir = "/lib/firmware/"

dir = Dir["/lib/modules/*"].first
puts "Scanning kernel modules in #{dir}..."

# list of referenced firmware names from the kernel modules
fw = []

Find.find(dir) do |path|
  if File.file?(path) && path.end_with?(".ko", ".ko.xz", ".ko.zst")
    fw += `/usr/sbin/modinfo -F firmware #{path.shellescape}`.split("\n")
  end
end

unused_size = 0

Find.find(fw_dir) do |fw_path|
  next unless File.file?(fw_path)

  fw_name = fw_path.delete_prefix(fw_dir).delete_suffix(".xz").delete_suffix(".zstd")

  if !fw.include?(fw_name)
    unused_size += File.size(fw_path)
    if (ARGV[0] == "--delete")
      puts "Deleting firmware file #{fw_path}"
      File.delete(fw_path)
    else
      puts "Found unused firmware #{fw_path}"
    end
  end
end

puts "Unused firmware size: #{unused_size} (#{unused_size/1024/1024} MiB)"
