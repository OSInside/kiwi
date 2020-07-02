buildroot = /

SRCS := $(wildcard *.c)
PRGS := $(patsubst %.c,%,$(SRCS))

CC = gcc

all: $(PRGS)

%.o: %.c
	$(CC) $(CFLAGS) $< -o $@

clean:
	$(RM) $(PRGS)

install:
	install -d -m 755 ${buildroot}usr/bin
	install -m 755 $(PRGS) ${buildroot}usr/bin
