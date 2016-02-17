buildroot = /
bin_prefix = ${buildroot}/usr/bin
man_prefix = ${buildroot}/usr/share/man

CC = gcc -Wall -fpic -O2
LC = LC_MESSAGES

version := $(shell python3 -c 'from kiwi.version import __version__; print(__version__)')

TOOLS_OBJ = tools_bin tools_bin/startshell tools_bin/setctsid tools_bin/dcounter tools_bin/driveready tools_bin/utimer tools_bin/kversion tools_bin/isconsole tools_bin/kiwicompat

pep8:
	helper/run-pep8

.PHONY: test
test:
	nosetests --with-coverage --cover-erase --cover-package=kiwi --cover-xml
	helper/coverage-check

coverage:
	nosetests --with-coverage --cover-erase --cover-package=kiwi --cover-xml
	mv test/unit/coverage.xml test/unit/coverage.reference.xml

list_tests:
	@for i in test/unit/*_test.py; do basename $$i;done | sort

%.py:
	nosetests $@

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

man:
	${MAKE} -C doc man

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

po_status:
	./.fuzzy

.PHONY: completion
completion:
	mkdir -p completion && helper/completion_generator > completion/kiwi.sh

build: pep8 test completion po man
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

clean:
	find -name *.pyc | xargs rm -f
	find -name kiwi.mo | xargs rm -f
	rm -rf build
	rm -rf dist
	rm -rf tools_bin
