
#include <stdio.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <stdlib.h>
#include <unistd.h>

static int
inst_start_shell (char *tty_tv) {
    char  *args_apci [] = { "bash", 0 };
    char  *env_pci [] =   {
        "TERM=linux",
        "PS1=`pwd -P` # ",
        "HOME=/",
        "HISTFILE=",
        "PATH=/lbin:/bin:/sbin:/usr/bin:/usr/sbin", 0
    };
    int fd_ii;
    int sh_pid = fork ();

    if (sh_pid != 0)
    return sh_pid;    /* parent */

    fclose (stdin);
    fclose (stdout);
    fclose (stderr);
    setsid ();
    fd_ii = open (tty_tv, O_RDWR);
    ioctl (fd_ii, TIOCSCTTY, (void *)1);
    (void)dup (fd_ii);
    (void)dup (fd_ii);

    execve ("/bin/bash", args_apci, env_pci);
    fprintf (stderr, "Couldn't start shell (errno = %d)\n", errno);
    exit (-1);
    /*NOTREACHED*/
    return 0;
}

int main(int argc, char **argv) {
    int i;
    int last_pid = 0;
    for (i=1; i<argc; i++) {
        last_pid = inst_start_shell (argv[i]);
    }
    printf ("%d\n", last_pid);
    return 0;
}
