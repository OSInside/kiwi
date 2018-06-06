buildroot = /
python_version = 3
python_lookup_name = python$(python_version)
python = $(shell which $(python_lookup_name))

LC = LC_MESSAGES

version := $(shell \
    $(python) -c \
    'from kiwi.version import __version__; print(__version__)'\
)

.PHONY: test
test:
	tox -e unit_py3_4
	tox -e unit_py3_6

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
	# dracut modules
	install -d -m 755 ${buildroot}usr/lib/dracut/modules.d
	cp -a dracut/modules.d/* ${buildroot}usr/lib/dracut/modules.d
	# manual pages
	install -d -m 755 ${buildroot}usr/share/man/man8
	for man in doc/build/man/*.8; do \
		test -e $$man && gzip -f $$man || true ;\
	done
	for man in doc/build/man/*.8.gz; do \
		install -m 644 $$man ${buildroot}usr/share/man/man8 ;\
	done
	# completion
	install -d -m 755 ${buildroot}etc/bash_completion.d
	$(python) helper/completion_generator \
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
	# XML parser code is auto generated from schema using generateDS
	# http://pythonhosted.org/generateDS
	# ---
	# a) modify arch-name xsd:token pattern to be generic because
	#    generateDS translates the regular expression into another
	#    expression which is different and wrong compared to the
	#    expression in the schema
	cat kiwi/schema/kiwi.rnc | sed -e \
		s'@arch-name = xsd:token.*@arch-name = xsd:token {pattern = ".*"}@' >\
		kiwi/schema/kiwi_modified_for_generateDS.rnc
	# convert schema rnc format into xsd format and call generateDS
	trang -I rnc -O xsd kiwi/schema/kiwi_modified_for_generateDS.rnc \
		kiwi/schema/kiwi_for_generateDS.xsd
	generateDS.py -f --external-encoding='utf-8' --no-dates --no-warnings \
		-o kiwi/xml_parse.py kiwi/schema/kiwi_for_generateDS.xsd
	rm kiwi/schema/kiwi_for_generateDS.xsd
	rm kiwi/schema/kiwi_modified_for_generateDS.rnc

obs_test_status:
	./.obs_test_status

valid:
	for i in `find build-tests test kiwi -name *.xml -o -name *.kiwi`; do \
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

build: clean tox
	# create setup.py variant for rpm build.
	# delete module versions from setup.py for building an rpm
	# the dependencies to the python module rpm packages is
	# managed in the spec file
	sed -ie "s@>=[0-9.]*'@'@g" setup.py
	# build the sdist source tarball
	$(python) setup.py sdist
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

pypi: clean tox
	$(python) setup.py sdist upload

clean: clean_git_attributes
	rm -rf dist
	rm -rf build
	${MAKE} -C tools clean
