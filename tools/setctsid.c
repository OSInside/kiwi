/*
 * setctsid.c -- execute a command in a new session and with
 *     new controlling terminal
 *
 * derviated from: setctsid.c of Rick Sladkey <jrs@world.std.com>
 *       In the public domain.
 *
 * Changed by Werner Fink, <werner@suse.de>
 */

#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/ioctl.h>
#include <sys/syslog.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <string.h>

#define xerror(n) do { int error = errno; \
                     if (!isatty(fileno(stderr))) \
                         syslog(LOG_ERR, n ": %s", strerror(error)); \
                     else \
                         errno = error, perror(n); \
            } while (0)

int main(int argc, char *argv[])
{
    int fd;
    struct stat buf;
    int dofork = 0;

                if (argc > 1 && !strcmp(argv[1], "-f")) {
        dofork = 1;
        argc--;
        argv++;
    }
    if (argc < 3) {
        fprintf(stderr, "usage: setctsid [-f] tty program [arg ...]\n");
        exit(1);
    }
    if (stat(argv[1], &buf) < 0) {
        perror(argv[1]);
        exit(1);
    }
    if (!(S_ISCHR(buf.st_mode))) {
        /* why do we care? */
        fprintf(stderr, "%s: not a character device\n", argv[1]);
        exit(1);
    }
    if (dofork) {
        switch (fork()) {
        case -1:
            perror("fork");
            exit(1);
        case 0:
            break;
        default:
            exit(0);
        }
    }
    if (setsid() < 0) {
        perror("setsid");
        exit(1);
    }
    if ((fd = open(argv[1], O_RDWR, 0)) < 0) {
        xerror("open");
        exit(1);
    }
    dup2(fd, fileno(stdin));
    dup2(fd, fileno(stdout));
    dup2(fd, fileno(stderr));

    if (isatty(fd)) {
        if (ioctl(fileno(stdin), TIOCSCTTY, argv[1]) < 0) {
            xerror("ioctl");
            exit(1);
        }
    }

    if (fd > fileno(stderr))
        close(fd);

    execvp(argv[2], argv + 2);
    xerror("execvp");
    exit(1);
}
