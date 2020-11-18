#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv) {
    int i, percent = -1;
    int newline = 0;
    const int max_prefix_len = 512;
    char prefix[max_prefix_len];
    unsigned cnt = 0, blk_size = 1024*1024, blk_cnt = 0, size = 0;
    ssize_t r;
    char buf[1024*1024];
    argv++; argc--;
    memset (prefix,'\0',max_prefix_len);
    if (argc > 1 && strstr(*argv, "-s")) {
        i = atoi(argv[1]);
        if (i) {
            size = i;
        }
        argv += 2;
        argc -= 2;
    }
    if (argc == 2 && strstr(*argv, "-l")) {
        newline = 1;
        strncpy (prefix, *(argv+1), max_prefix_len - 1);
    }
    if (!size) {
        fprintf(stderr, "no size in MB set\n");
        return 1;
    }
    fprintf(stderr, "      ");
    while((r = read(0, buf, sizeof buf)) > 0) {
        ssize_t p = 0;
        ssize_t w = 0;
        while((w = write(1, buf + p, r - p)) >= 0) {
            p += w;
            if(p >= r) {
                break;
            }
        }
        if(p < r) {
            fprintf(stderr, "write error\n");
            return 1;
        }
        cnt += r;
        if(cnt >= blk_size) {
            blk_cnt += cnt / blk_size;
            cnt %= blk_size;
            i = percent;
            percent = (blk_cnt * 100) / size;
            if(percent != i) {
                if (newline) {
                    fprintf(stderr, "%s(%3d%%)\n",prefix, percent);
                } else {
                    fprintf(stderr, "\x08\x08\x08\x08\x08\x08(%3d%%)", percent);
                }
            }
        }
    }
    fflush(stdout);
    return 0;
}
