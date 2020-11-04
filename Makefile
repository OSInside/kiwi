buildroot = /
docdir = /usr/share/doc/packages
python_version = 3
python_lookup_name = python$(python_version)
python = $(shell which $(python_lookup_name))

LC = LC_MESSAGES

version := $(shell \
    $(python) -c \
    'from kiwi.version import __version__; print(__version__)'\
)

.PHONY: tools
tools:
	# apart from python sources there are also some legacy
	# C tools used in custom kiwi boot descriptions.
	# Note: These information will be missing when installed from pip
	${MAKE} -C tools all

install_dracut:
	install -d -m 755 ${buildroot}usr/lib/dracut/modules.d
	cp -a dracut/modules.d/* ${buildroot}usr/lib/dracut/modules.d

install_package_docs:
	install -d -m 755 ${buildroot}${docdir}/python-kiwi
	install -m 644 doc/build/latex/kiwi.pdf \
		${buildroot}${docdir}/python-kiwi/kiwi.pdf
	install -m 644 LICENSE \
		${buildroot}${docdir}/python-kiwi/LICENSE
	install -m 644 README.rst \
		${buildroot}${docdir}/python-kiwi/README

install:
	# apart from python sources there are also
	# the C tools, the manual pages and the completion
	# Note: These information will be missing when installed from pip
	${MAKE} -C tools buildroot=${buildroot} install
	# manual pages
	install -d -m 755 ${buildroot}usr/share/man/man8
	for man in doc/build/man/*.8; do \
		test -e $$man && gzip -f $$man || true ;\
	done
	for man in doc/build/man/*.8.gz; do \
		install -m 644 $$man ${buildroot}usr/share/man/man8 ;\
	done
	# completion
	install -d -m 755 ${buildroot}usr/share/bash-completion/completions
	$(python) helper/completion_generator.py \
		> ${buildroot}usr/share/bash-completion/completions/kiwi-ng
	# kiwi default configuration
	install -d -m 755 ${buildroot}etc
	install -m 644 kiwi.yml ${buildroot}etc/kiwi.yml

tox:
	tox "-n 5"

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
	# append PDF documentation to tarball
	gzip -d dist/python-kiwi.tar.gz
	mkdir -p kiwi-${version}/doc/build/latex
	mv doc/build/latex/kiwi.pdf kiwi-${version}/doc/build/latex
	tar -uf dist/python-kiwi.tar kiwi-${version}/doc/build/latex/kiwi.pdf
	gzip dist/python-kiwi.tar
	rm -rf kiwi-${version}
	# update rpm changelog using reference file
	helper/update_changelog.py --since package/python-kiwi.changes > \
		dist/python-kiwi.changes
	helper/update_changelog.py --file package/python-kiwi.changes >> \
		dist/python-kiwi.changes
	# update package version in spec file
	cat package/python-kiwi-spec-template | sed -e s'@%%VERSION@${version}@' \
		> dist/python-kiwi.spec
	# update package version in PKGBUILD file
	md5sums=$$(md5sum dist/python-kiwi.tar.gz | cut -d" " -f1); \
	cat package/python-kiwi-pkgbuild-template | sed -e s'@%%VERSION@${version}@' \
		-e s"@%%MD5SUM@$${md5sums}@" > dist/PKGBUILD
	# provide rpm rpmlintrc
	cp package/python-kiwi-rpmlintrc dist

pypi: clean tox
	$(python) setup.py sdist upload

clean: clean_git_attributes
	$(python) setup.py clean
	rm -rf doc/build
	rm -rf doc/dist
	${MAKE} -C tools clean
