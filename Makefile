buildroot = /

LC = LC_MESSAGES

version := $(shell \
    python3 -c 'from kiwi.version import __version__; print(__version__)'\
)

.PHONY: test
test:
	tox -e 3.4

flake:
	tox -e check

.PHONY: tools
tools:
	# apart from all python source we need to compile the
	# C tools. see setup.py for details when this target is
	# called
	${MAKE} -C tools all

install:
	# apart from all python source we also need to install
	# the C tools, the manual pages and the completion
	# see setup.py for details when this target is called
	${MAKE} -C tools buildroot=${buildroot} install
	# manual pages
	install -d -m 755 ${buildroot}usr/share/man/man2
	for man in doc/build/man/*.2; do \
		gzip -f $$man && \
		install -m 644 $$man.gz ${buildroot}usr/share/man/man2 ;\
	done
	# completion
	install -d -m 755 ${buildroot}etc/bash_completion.d
	install -m 644 completion/kiwi-ng.sh \
		${buildroot}etc/bash_completion.d

tox:
	tox

kiwi/schema/kiwi.rng: kiwi/schema/kiwi.rnc
	# whenever the schema is changed this target will convert
	# the short form of the RelaxNG schema to the format used
	# in code and auto generates the python data structures
	trang -I rnc -O rng kiwi/schema/kiwi.rnc kiwi/schema/kiwi.rng
	trang -I rnc -O xsd kiwi/schema/kiwi.rnc kiwi/schema/kiwi.xsd
	# XML parser code is auto generated from schema using generateDS
	# http://pythonhosted.org/generateDS
	generateDS.py -f --external-encoding='utf-8' \
		-o kiwi/xml_parse.py kiwi/schema/kiwi.xsd
	rm kiwi/schema/kiwi.xsd

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
	mkdir -p completion && helper/completion_generator > completion/kiwi-ng.sh

build: clean completion po tox
	# the following is required to update the $Format:%H$ git attribute
	git archive HEAD kiwi/version.py | tar -x
	# now create my package sources
	cat setup.py | sed -e "s@>=[0-9.]*'@'@g" > setup.build.py
	python3 setup.build.py sdist
	# go back to origin template of version.py
	git checkout kiwi/version.py
	mv dist/kiwi-${version}.tar.bz2 dist/python3-kiwi.tar.bz2
	rm setup.build.py
	git log | helper/changelog_generator |\
		helper/changelog_descending > dist/python3-kiwi.changes
	cat package/python3-kiwi-spec-template | sed -e s'@%%VERSION@${version}@' \
		> dist/python3-kiwi.spec
	cp package/python3-kiwi-rpmlintrc dist
	helper/kiwi-boot-packages > dist/python3-kiwi-boot-packages

clean:
	rm -rf dist
	rm -rf build
	rm -rf completion
	${MAKE} -C tools clean
