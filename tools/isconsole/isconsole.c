#include <stdio.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <linux/kd.h>
#include <unistd.h>
#include <errno.h>

int main (void) {
    int mode = 0;
    int status;
    int tty  = open( "/dev/console", O_RDONLY );
    if (tty < 0) {
        // failed to open device
        return 1;
    }
    status = ioctl( tty, KDGETMODE, &mode );
    close (tty);
    if (status != 0) {
        // ioctl returned error
        return 1;
    }
    return 0;
}
