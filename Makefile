buildroot = /

kiwi_prefix = ${buildroot}/usr/share/kiwi
bin_prefix  = ${buildroot}/usr/bin

TOOLSVZ     = ${bin_prefix}
LIVESTICKVZ = ${kiwi_prefix}/livestick

CC  = gcc -Wall -fpic -O2

TOOLS_OBJ = tools_bin tools_bin/startshell tools_bin/setctsid tools_bin/dcounter tools_bin/driveready tools_bin/utimer tools_bin/kversion tools_bin/isconsole

pep8:
	helper/run-pep8

.PHONY: test
test:
	./.version > kiwi/schema/kiwi.revision
	nosetests --with-coverage --cover-erase --cover-package=kiwi --cover-xml
	helper/coverage-check

coverage:
	nosetests --with-coverage --cover-erase --cover-package=kiwi --cover-xml
	mv test/unit/coverage.xml test/unit/coverage.reference.xml

list_tests:
	@for i in test/unit/*_test.py; do basename $$i;done | sort

%.py:
	nosetests $@

kiwi/xml_parse.py: kiwi/schema/kiwi.xsd
	# XML parser code is auto generated from schema using generateDS
	# http://pythonhosted.org/generateDS
	generateDS.py --external-encoding='utf-8' \
		-o kiwi/xml_parse.py kiwi/schema/kiwi.xsd

kiwi/schema/kiwi.xsd: kiwi/schema/kiwi.rnc
	trang -I rnc -O xsd kiwi/schema/kiwi.rnc kiwi/schema/kiwi.xsd

tools_bin:
	mkdir -p tools_bin

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

install_tools:
	cp -a tools_bin/* ${TOOLSVZ}
	cp -a tools/livestick/theme ${LIVESTICKVZ}
	install -m 755 tools/livestick/livestick ${TOOLSVZ}

clean:
	find -name *.pyc | xargs rm -f
	rm -rf build
	rm -rf dist
	rm -rf tools_bin
