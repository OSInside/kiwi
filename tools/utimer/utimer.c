#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>

#define PATH_DEV_NULL "/dev/null"

static double time_start = 0;
void printTime (int);

int main (void) {
    struct timeval tv;
    int child;
    FILE* fd;
    gettimeofday (&tv,NULL);
    time_start = tv.tv_sec + tv.tv_usec*1E-6;
    signal (SIGHUP,printTime);
    child = fork();
    switch (child) {
        case -1:
            printf ("%d\n",-1);
            exit (-1);
        case 0:
            // child waiting for signals
            while (1) {
                pause();
            }
        default:
            // parent exiting with child pid
            if ((fd = fopen ("/var/run/utimer.pid","w")) == NULL) {
                kill (child,SIGTERM); exit (1);
            }
            fprintf (fd,"%d\n",child);
            fclose (fd);
            exit (0);
    }
    return 0;
}

void printTime (int s) {
    struct timeval tv;
    double time_next;
    FILE* fd;
    gettimeofday (&tv,NULL);
    time_next = tv.tv_sec + tv.tv_usec*1E-6 - time_start;
    if ((fd = fopen ("/tmp/utimer","w")) != NULL) {
        fprintf (fd,"[%12f]\n",time_next);
        fclose (fd);
    }
}

