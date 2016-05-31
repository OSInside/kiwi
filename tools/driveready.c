#include <stdio.h>
#include <scsi/sg.h>
#include <scsi/scsi.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

static void print_hex (const unsigned char*, int);

static void print_hex(const unsigned char *p, int len) {
    int i;
    for (i = 0; i < len; i++) {
        if (i % 16 == 0) {
            fprintf (stderr,"%04x: ", i);
        }
        fprintf (stderr,"%02x", p[i]);
        if (i % 4 == 3) {
            if (i % 16 == 15) {
                fprintf (stderr,"\n");
            } else {
                fprintf (stderr,"  ");
            }
        } else {
            fprintf (stderr," ");
        }
    }
    if (len % 16) {
        fprintf (stderr,"\n");
    }
}

int main(int argc, char **argv) {
    struct sg_io_hdr transport = { };
    unsigned char cmd[] = { 0, 0, 0, 0, 0, 0 };
    unsigned char sense_data[32] = { };
    int fd, rc;

    if (argc < 2) {
        fprintf(stderr, "Usage: wait-ready DEVICE\n");
        return 1;
    }

    fd = open(argv[1], O_RDONLY|O_NONBLOCK);
    if (fd < 0) {
        perror("open");
        return 1;
    }

    transport.interface_id = 'S';
    transport.cmdp = cmd;
    transport.cmd_len = sizeof(cmd);
    transport.sbp = sense_data;
    transport.mx_sb_len = sizeof(sense_data);
    transport.dxfer_direction = SG_DXFER_NONE;

    rc = ioctl(fd, SG_IO, &transport);
    if (rc) {
        perror("ioctl(SG_IO)");
        return 1;
    }

    if ((transport.masked_status & CHECK_CONDITION) && transport.sb_len_wr) {
        fprintf(stderr,"* check sense data:\n");
        print_hex (sense_data, sizeof(sense_data));
        fprintf (stderr,"SK=0x%02x ASC=0x%02x ASCQ=0x%02x\n",
            sense_data[2], sense_data[12], sense_data[13]
        );
        return 1;
    }
    return 0;
}
