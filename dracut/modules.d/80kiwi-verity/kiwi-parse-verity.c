// vi: set sw=4 ts=4 :
// SPDX-License-Identifier: GPL-2.0-or-later
// Copyright (C) 2023 Canonical Ltd
// Author: Isaac True <isaac.true@canonical.com>
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

#define _POSIX_C_SOURCE (200809L)
#define _LARGEFILE64_SOURCE

#include <inttypes.h>
#include <sys/types.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <stdint.h>
#include <stdbool.h>
#include <assert.h>
#include <fcntl.h>
#include <ctype.h>

enum output_type {
    OUTPUT_VERSION,
    OUTPUT_FSTYPE,
    OUTPUT_ACCESS,
    OUTPUT_IDENTIFIER,
    OUTPUT_HASH_TYPE,
    OUTPUT_DATA_BLOCK_SIZE,
    OUTPUT_HASH_BLOCK_SIZE,
    OUTPUT_DATA_BLOCKS,
    OUTPUT_HASH_START_BLOCK,
    OUTPUT_ALGORITHM,
    OUTPUT_ROOT_HASH,
    OUTPUT_SALT,
    OUTPUT_UNKNOWN,
};

struct args {
    char *path;
    uint64_t block_size;
    uint64_t end_offset;
    bool verbose;
    enum output_type output;
};

struct kiwi_verity_header {
    /* currently set to 1 */
    char version;
    /* name of filesystem attribute */
    char *fstype;
    /* either ro or rw depending on the filesystem capabilities */
    char *access;
    /* fixed identifier value */
    char *identifier;
};

struct kiwi_verity_metadata {
    /* hash type name as returned by veritysetup */
    char hash_type;
    /* data blocksize as returned by veritysetup */
    char *data_blksize;
    /* hash blocksize as returned by veritysetup */
    char *hash_blksize;
    /* number of data blocks as returned by veritysetup */
    char *data_blocks;
    /* hash start block as required by the kernel to construct the device map */
    char *hash_start_block;
    /* hash algorithm as returned by veritysetup */
    char *algorithm;
    /* root hash as returned by veritysetup */
    char *root_hash;
    /* salt hash as returned by veritysetup */
    char *salt;
};

static const char *const output_table[] = {
    [OUTPUT_VERSION] = "version",
    [OUTPUT_FSTYPE] = "fs-type",
    [OUTPUT_ACCESS] = "access",
    [OUTPUT_IDENTIFIER] = "identifier",
    [OUTPUT_HASH_TYPE] = "hash-type",
    [OUTPUT_DATA_BLOCK_SIZE] = "data-blocksize",
    [OUTPUT_HASH_BLOCK_SIZE] = "hash-blocksize",
    [OUTPUT_DATA_BLOCKS] = "data-blocks",
    [OUTPUT_HASH_START_BLOCK] = "hash-start-block",
    [OUTPUT_ALGORITHM] = "algorithm",
    [OUTPUT_ROOT_HASH] = "root-hash",
    [OUTPUT_SALT] = "salt",
};

static void print_usage(char *const argv[]);
static enum output_type parse_output_type(const char *const str);
static int parse_args(struct args *const args, const int argc,
        char *const argv[]);
static int kiwi_read_verity_info(const struct args *const args,
        struct kiwi_verity_header *const header,
        struct kiwi_verity_metadata *const metadata);
static bool is_data_separator(char c);
static int read_string(int fd, char **const dest);
static int read_char(int fd, char *const dest);
static void cleanup(struct kiwi_verity_header *const header,
        struct kiwi_verity_metadata *const metadata);

static enum output_type parse_output_type(const char *const str)
{
    char buffer[32] = {'\0'};

    assert(str);

    /*
     * Copy the string to a temporary buffer so we can ensure it's
     * NULL-terminated.
     */
    memcpy(buffer, str, strnlen(str, sizeof(buffer) - 1));
    buffer[sizeof(buffer) - 1] = '\0';

    for (size_t i = 0; i < (sizeof(output_table) / sizeof(output_table[0]));
        i++) {
        if (!memcmp(buffer, output_table[i],
            strnlen(output_table[i], sizeof(buffer) - 1) + 1)) {
            return (enum output_type)i;
        }
    }

    return OUTPUT_UNKNOWN;
}

static int parse_args(struct args *const args, const int argc,
        char *const argv[])
{
    int c;

    assert(args);
    assert(argc > 0);
    assert(argv);

    while ((c = getopt(argc, argv, "p:b:e:vo:")) != -1)
        switch (c) {
            case 'p':
                args->path = optarg;
                break;
            case 'b':
                args->block_size = strtoul(optarg, NULL, 10);
                break;
            case 'e':
                args->end_offset = strtoul(optarg, NULL, 10);
                break;
            case 'v':
                args->verbose = true;
                break;
            case 'o':
                args->output = parse_output_type(optarg);
                break;
            case '?':
                return 1;
            default:
                print_usage(argv);
                return 1;
        }

    return 0;
}

static void print_usage(char *const argv[])
{
    assert(argv);

    puts("kiwi-parse-verity");
    puts("Tool for extracting verity information from a Kiwi image");
    puts("Written by Isaac True <isaac.true@canonical.com>");
    puts("");
    printf("Usage: %s -p <path> [options]\n", argv[0]);
    puts(" -p <path>: path to the device where the verity data is stored");
    puts(" -o <output type>: data to extract (default root-hash). Can be one of the following:");

    for (size_t i = 0; i < (sizeof(output_table) / sizeof(output_table[0]));
            i++) {
        printf("      %s\n", output_table[i]);
    }

    puts(" -e <offset>: offset in blocks from the end of the target device where the data is stored (default 1)");
    puts(" -b <block size>: hash block size (default 4096)");
    puts(" -v: enable verbose mode");
}

static int kiwi_read_verity_info(const struct args *const args,
        struct kiwi_verity_header *const header,
        struct kiwi_verity_metadata *const metadata)
{
    int fd;
    int ret;
    off64_t offset;

    assert(args);
    assert(header);
    assert(metadata);

    fd = open(args->path, O_RDONLY);
    if (fd < 0) {
        printf("Failed to open %s: %s (%d)\n", args->path,
                strerror(errno), errno);
        return -errno;
    }

    offset = (off64_t)args->block_size * (off64_t)args->end_offset;
    if (lseek64(fd, -offset, SEEK_END) < 0) {
        printf("Failed to go to offset %"PRIu64" in %s: %s (%d)\n", offset,
                args->path, strerror(errno), errno);
        return -errno;
    }

    /*
     * Make sure that we are parsing a known version. This also serves as
     * a basic preliminary sanity check.
     */
    ret = read_char(fd, &header->version);
    if (ret < 0) {
        return ret;
    }

    if (header->version != '1') {
        printf("Invalid Kiwi verity metadata version: %c\n",
                header->version);
        return -EINVAL;
    }

    ret = read_string(fd, &header->fstype);
    if (ret < 0) {
        return ret;
    }
    ret = read_string(fd, &header->access);
    if (ret < 0) {
        return ret;
    }
    ret = read_string(fd, &header->identifier);
    if (ret < 0) {
        return ret;
    }

    ret = read_char(fd, &metadata->hash_type);
    if (ret < 0) {
        return ret;
    }
    ret = read_string(fd, &metadata->data_blksize);
    if (ret < 0) {
        return ret;
    }
    ret = read_string(fd, &metadata->hash_blksize);
    if (ret < 0) {
        return ret;
    }
    ret = read_string(fd, &metadata->data_blocks);
    if (ret < 0) {
        return ret;
    }
    ret = read_string(fd, &metadata->hash_start_block);
    if (ret < 0) {
        return ret;
    }
    ret = read_string(fd, &metadata->algorithm);
    if (ret < 0) {
        return ret;
    }
    ret = read_string(fd, &metadata->root_hash);
    if (ret < 0) {
        return ret;
    }
    ret = read_string(fd, &metadata->salt);
    if (ret < 0) {
        return ret;
    }

    close(fd);

    return 0;
}

static bool is_data_separator(char c)
{
    return (c == ' ' || c == '\xff');
}

static int read_string(int fd, char **const dest)
{
    char buffer[256] = {'\0'};
    size_t i = 0;

    assert(fd >= 0);
    assert(dest);

    do {
        ssize_t ret = read(fd, &buffer[i], 1);
        if (ret < 0) {
            return -errno;
        } else if (ret < 1) {
            return -ENOSPC;
        }

        if (is_data_separator(buffer[i])) {
            /* End the string here */
            buffer[i] = '\0';
            break;
        }

    } while (i++ < (sizeof(buffer) - 1));

    *dest = strdup(buffer);
    if (!*dest) {
        return -errno;
    }

    return 0;
}

static int read_char(int fd, char *const dest)
{
    char *buffer = NULL;
    int ret;

    assert(fd >= 0);
    assert(dest);

    ret = read_string(fd, &buffer);
    if (ret < 0) {
        return 0;
    }

    assert(buffer);

    *dest = buffer[0];
    free(buffer);

    return 0;
}

static void cleanup(struct kiwi_verity_header *const header,
        struct kiwi_verity_metadata *const metadata)
{
    assert(header);
    assert(metadata);

    if (header->access != NULL) {
        free(header->access);
    }
    if (header->fstype != NULL) {
        free(header->fstype);
    }
    if (header->identifier != NULL) {
        free(header->identifier);
    }
    if (metadata->algorithm != NULL) {
        free(metadata->algorithm);
    }
    if (metadata->data_blksize != NULL) {
        free(metadata->data_blksize);
    }
    if (metadata->data_blocks != NULL) {
        free(metadata->data_blocks);
    }
    if (metadata->hash_blksize != NULL) {
        free(metadata->hash_blksize);
    }
    if (metadata->hash_start_block != NULL) {
        free(metadata->hash_start_block);
    }
    if (metadata->root_hash != NULL) {
        free(metadata->root_hash);
    }
    if (metadata->salt != NULL) {
        free(metadata->salt);
    }
}

int main(int argc, char *argv[])
{
    int ret = 0;
    struct args args = {
        .path = NULL,
        .block_size = 4096,
        .end_offset = 1,
        .verbose = false,
        .output = OUTPUT_ROOT_HASH,
    };
    struct kiwi_verity_header header = {0};
    struct kiwi_verity_metadata metadata = {0};

    ret = parse_args(&args, argc, argv);
    if (ret) {
        return ret;
    }

    if (args.path == NULL || args.output == OUTPUT_UNKNOWN ||
            args.block_size == 0 || args.end_offset == 0) {
        print_usage(argv);
        return -1;
    }

    if (args.verbose) {
        printf("Reading from %s, block size %"PRIu64", block offset from end %"PRIu64"\n",
                args.path, args.block_size, args.end_offset);
    }

    ret = kiwi_read_verity_info(&args, &header, &metadata);
    if (ret) {
        printf("Failed to read metadata: %s (%d)\n", strerror(-ret),
                ret);
        goto exit;
    }

    if (args.verbose) {
        printf("\nHeader:\n");
        printf("  Version: %c\n", header.version);
        printf("  FS Type: %s\n", header.fstype);
        printf("  Access: %s\n", header.access);
        printf("  Identifier: %s\n", header.identifier);
        printf("\nMetadata:\n");
        printf("  Hash type: %c\n", metadata.hash_type);
        printf("  Data blksize: %s\n", metadata.data_blksize);
        printf("  Hash blksize: %s\n", metadata.hash_blksize);
        printf("  Data blocks: %s\n", metadata.data_blocks);
        printf("  Hash start block: %s\n", metadata.hash_start_block);
        printf("  Algorithm: %s\n", metadata.algorithm);
        printf("  Root hash: %s\n", metadata.root_hash);
        printf("  Salt: %s\n", metadata.salt);
    }

    switch (args.output) {
        case OUTPUT_VERSION:
            printf("%c\n", header.version);
            break;
        case OUTPUT_FSTYPE:
            printf("%s\n", header.fstype);
            break;
        case OUTPUT_ACCESS:
            printf("%s\n", header.access);
            break;
        case OUTPUT_IDENTIFIER:
            printf("%s\n", header.identifier);
            break;
        case OUTPUT_HASH_TYPE:
            printf("%c\n", metadata.hash_type);
            break;
        case OUTPUT_DATA_BLOCK_SIZE:
            printf("%s\n", metadata.data_blksize);
            break;
        case OUTPUT_HASH_BLOCK_SIZE:
            printf("%s\n", metadata.hash_blksize);
            break;
        case OUTPUT_DATA_BLOCKS:
            printf("%s\n", metadata.data_blocks);
            break;
        case OUTPUT_HASH_START_BLOCK:
            printf("%s\n", metadata.hash_start_block);
            break;
        case OUTPUT_ALGORITHM:
            printf("%s\n", metadata.algorithm);
            break;
        case OUTPUT_ROOT_HASH:
            printf("%s\n", metadata.root_hash);
            break;
        case OUTPUT_SALT:
            printf("%s\n", metadata.salt);
            break;
        default:
            return -1;
    }

exit:
    cleanup(&header, &metadata);
    return ret;
}
