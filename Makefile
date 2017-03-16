buildroot = /
python_version = 3

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
		test -e $$man && gzip -f $$man || true ;\
	done
	for man in doc/build/man/*.2.gz; do \
		install -m 644 $$man ${buildroot}usr/share/man/man2 ;\
	done
	# completion
	install -d -m 755 ${buildroot}etc/bash_completion.d
	helper/completion_generator \
		> ${buildroot}etc/bash_completion.d/kiwi-ng-${python_version}.sh
	# license
	install -d -m 755 ${buildroot}/usr/share/doc/packages/python-kiwi
	install -m 644 LICENSE \
		${buildroot}/usr/share/doc/packages/python-kiwi/LICENSE
	install -m 644 README.rst \
		${buildroot}/usr/share/doc/packages/python-kiwi/README

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

git_attributes:
	# the following is required to update the $Format:%H$ git attribute
	# for details on when this target is called see setup.py
	git archive HEAD kiwi/version.py | tar -x

clean_git_attributes:
	# cleanup version.py to origin state
	# for details on when this target is called see setup.py
	git checkout kiwi/version.py

sdist_prepare:
	# build the architecture specific boot image structure
	tar --dereference -czf boot_arch.tgz kiwi/boot/arch && \
		mv kiwi/boot/arch boot_arch && mkdir kiwi/boot/arch

build: clean po tox sdist_prepare
	# create setup.py variant for rpm build.
	# delete module versions from setup.py for building an rpm
	# the dependencies to the python module rpm packages is
	# managed in the spec file
	sed -ie "s@>=[0-9.]*'@'@g" setup.py
	# build the sdist source tarball
	python3 setup.py sdist
	# cleanup sdist_prepare actions
	rm -f boot_arch.tgz && \
		rmdir kiwi/boot/arch && mv boot_arch kiwi/boot/arch
	# restore original setup.py backed up from sed
	mv setup.pye setup.py
	# provide rpm source tarball
	mv dist/kiwi-${version}.tar.gz dist/python-kiwi.tar.gz
	# provide rpm changelog from git changelog
	git log | helper/changelog_generator |\
		helper/changelog_descending > dist/python-kiwi.changes
	# update package version in spec file
	cat package/python-kiwi-spec-template | sed -e s'@%%VERSION@${version}@' \
		> dist/python-kiwi.spec
	# provide rpm rpmlintrc
	cp package/python-kiwi-rpmlintrc dist
	# provide rpm boot packages source
	# metadata for the buildservice when kiwi is used in the
	# buildservice this data is needed
	helper/kiwi-boot-packages > dist/python-kiwi-boot-packages

pypi: clean po tox sdist_prepare
	python3 setup.py sdist upload
	rm -f boot_arch.tgz && \
		rmdir kiwi/boot/arch && mv boot_arch kiwi/boot/arch

clean: clean_git_attributes
	rm -rf dist
	rm -rf build
	${MAKE} -C tools clean
