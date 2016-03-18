buildroot = /
bin_prefix = ${buildroot}/usr/bin
man_prefix = ${buildroot}/usr/share/man

CC = gcc -Wall -fpic -O2
LC = LC_MESSAGES

version := $(shell python3 -c 'from kiwi.version import __version__; print(__version__)')

TOOLS_OBJ = tools_bin tools_bin/startshell tools_bin/setctsid tools_bin/dcounter tools_bin/driveready tools_bin/utimer tools_bin/kversion tools_bin/isconsole tools_bin/kiwicompat

.PHONY: test
test:
	tox -e 3.4

flake:
	tox -e check

%.py:
	tox -e 3.4_single $@

list_tests:
	@for i in test/unit/*_test.py; do basename $$i;done | sort

kiwi/schema/kiwi.rng: kiwi/schema/kiwi.rnc
	trang -I rnc -O rng kiwi/schema/kiwi.rnc kiwi/schema/kiwi.rng
	trang -I rnc -O xsd kiwi/schema/kiwi.rnc kiwi/schema/kiwi.xsd
	# XML parser code is auto generated from schema using generateDS
	# http://pythonhosted.org/generateDS
	generateDS.py -f --external-encoding='utf-8' \
		-o kiwi/xml_parse.py kiwi/schema/kiwi.xsd
	rm kiwi/schema/kiwi.xsd

tools_bin:
	mkdir -p tools_bin

tox:
	tox

tools: ${TOOLS_OBJ}

tools_bin/dcounter: tools/dcounter/dcounter.c
	${CC} ${CFLAGS} tools/dcounter/dcounter.c -o tools_bin/dcounter

tools_bin/startshell: tools/startshell/startshell.c
	${CC} ${CFLAGS} tools/startshell/startshell.c -o tools_bin/startshell

tools_bin/setctsid: tools/setctsid/setctsid.c
	${CC} ${CFLAGS} tools/setctsid/setctsid.c -o tools_bin/setctsid

tools_bin/driveready: tools/driveready/driveready.c
	${CC} ${CFLAGS} tools/driveready/driveready.c -o tools_bin/driveready

tools_bin/utimer: tools/utimer/utimer.c
	${CC} ${CFLAGS} tools/utimer/utimer.c -o tools_bin/utimer

tools_bin/kversion: tools/kversion/kversion.c
	${CC} ${CFLAGS} tools/kversion/kversion.c -o tools_bin/kversion

tools_bin/isconsole: tools/isconsole/isconsole.c
	${CC} ${CFLAGS} tools/isconsole/isconsole.c -o tools_bin/isconsole

tools_bin/kiwicompat: tools/kiwicompat/kiwicompat
	install -m 755 tools/kiwicompat/kiwicompat tools_bin/kiwicompat

install_tools:
	install -d -m 755 ${bin_prefix}
	cp -a tools_bin/* ${bin_prefix}

install_man:
	install -d -m 755 ${man_prefix}/man2
	for man in doc/build/man/*.2; do \
		gzip -f $$man && install -m 644 $$man.gz ${man_prefix}/man2 ;\
	done

po:
	./.locale
	for i in `ls -1 kiwi/boot/locale`; do \
		if [ -d ./kiwi/boot/locale/$$i ];then \
			if [ ! "$$i" = "kiwi-help" ] && [ ! "$$i" = "kiwi-template" ];then \
				(cd ./kiwi/boot/locale/$$i/${LC} && msgfmt -o kiwi.mo kiwi.po);\
			fi \
		fi \
	done
	for boot_arch in kiwi/boot/arch/*; do \
		if [ ! -L $$boot_arch ];then \
			for boot_image in $$boot_arch/*/*/root; do \
				mkdir -p $$boot_image/usr/share/locale ;\
				cp -a kiwi/boot/locale/* $$boot_image/usr/share/locale/ ;\
				rm -rf $$boot_image/usr/share/locale/kiwi-template ;\
				rm -rf $$boot_image/usr/share/locale/*/LC_MESSAGES/kiwi.po ;\
			done \
		fi \
	done

po_status:
	./.fuzzy

valid:
	for i in `find test kiwi -name *.xml`; do \
		if [ ! -L $$i ];then \
			xsltproc -o $$i.converted kiwi/xsl/master.xsl $$i && \
			mv $$i.converted $$i ;\
		fi \
	done

.PHONY: completion
completion:
	mkdir -p completion && helper/completion_generator > completion/kiwi.sh

build: completion po tox
	rm -f dist/*
	# the following is required to update the $Id$ git attribute
	rm kiwi/version.py && git checkout kiwi/version.py
	# now create my package sources
	cat setup.py | sed -e "s@>=[0-9.]*'@'@g" > setup.build.py
	python3 setup.build.py sdist
	mv dist/kiwi-${version}.tar.bz2 dist/python3-kiwi.tar.bz2
	rm setup.build.py
	git log | helper/changelog_generator |\
		helper/changelog_descending > dist/python3-kiwi.changes
	cat package/python3-kiwi-spec-template | sed -e s'@%%VERSION@${version}@' \
		> dist/python3-kiwi.spec
	cp package/python3-kiwi-rpmlintrc dist
	helper/kiwi-boot-packages > dist/python3-kiwi-boot-packages
