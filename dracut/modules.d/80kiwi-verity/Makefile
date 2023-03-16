buildroot ?= /

CROSS_COMPILE ?=
CC ?= $(CROSS_COMPILE)gcc
CFLAGS += -Werror -Wall -Wextra

BINARY := kiwi-parse-verity

.PHONY: all
all: build

.PHONY: install
install: build
	install -Dm0755 kiwi-verity-setup.sh module-setup.sh \
		-t ${buildroot}usr/lib/dracut/modules.d/80kiwi-verity
	install -Dm0755 $(BINARY) ${buildroot}usr/bin/$(BINARY)

.PHONY: build
build: $(BINARY)

.PHONY: clean
clean:
	rm -f $(BINARY)
