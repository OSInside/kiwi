buildroot = /
docdir = /usr/share/doc/packages
python_version = 3
python_lookup_name = python$(python_version)
python = $(shell which $(python_lookup_name))
sc_disable = SC1091,SC1090,SC2001,SC2174,SC1117,SC2048,SC2004

LC = LC_MESSAGES

version := $(shell \
    $(python) -c \
    'from kiwi.version import __version__; print(__version__)'\
)

install_dracut:
	for dracut in dracut/modules.d/*; do \
		${MAKE} -C $$dracut install ;\
	done

install_package_docs:
	install -d -m 755 ${buildroot}${docdir}/python-kiwi
	install -m 644 LICENSE \
		${buildroot}${docdir}/python-kiwi/LICENSE
	install -m 644 README.rst \
		${buildroot}${docdir}/python-kiwi/README

install:
	# apart from python sources there are also
	# the manual pages and the completion
	# Note: These information will be missing when installed from pip
	# manual pages
	install -d -m 755 ${buildroot}usr/share/man/man8
	for man in doc/build/man/*.8; do \
		install -m 644 $$man ${buildroot}usr/share/man/man8 ;\
	done
	# completion
	install -d -m 755 ${buildroot}usr/share/bash-completion/completions
	$(python) helper/completion_generator.py \
		> ${buildroot}usr/share/bash-completion/completions/kiwi-ng
	# kiwi default configuration
	install -d -m 755 ${buildroot}etc
	install -m 644 kiwi.yml ${buildroot}etc/kiwi.yml
	# kiwi old XSL stylesheets for upgrade
	install -d -m 755 ${buildroot}usr/share/kiwi
	cp -a helper/xsl_to_v74 ${buildroot}usr/share/kiwi/

kiwi/schema/kiwi.rng: kiwi/schema/kiwi.rnc
	# whenever the schema is changed this target will convert
	# the short form of the RelaxNG schema to the format used
	# in code and auto generates the python data structures
	@type -p trang &>/dev/null || \
		(echo "ERROR: trang not found in path: $(PATH)"; exit 1)
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

setup:
	poetry install --all-extras

docs: setup
	poetry run make -C doc man html

docs_suse: setup
	poetry run make -C doc xml
	rm -rf doc/build/restxml
	mv doc/build/xml doc/build/restxml
	poetry run pip install \
		git+https://github.com/openSUSE/rstxml2docbook.git@feature/kiwi
	poetry run bash -c 'pushd doc && rstxml2docbook \
		-v --no-split -o build/xml/book.xml build/restxml/index.xml'
	bash -c 'mkdir -p doc/build/images/src/png && \
		cp -a doc/source/.images/* doc/build/images/src/png'
	cp doc/DC-kiwi doc/build/
	bash -c 'pushd doc/build && daps -d DC-kiwi html'

test_scripts: setup
	poetry run bash -c \
		'pip install pytest-container && pushd test/scripts && pytest -s -vv'

check: setup
	# shell code checks
	bash -c 'shellcheck -e ${sc_disable} dracut/modules.d/*/*.sh -s bash'
	bash -c 'shellcheck -e ${sc_disable} kiwi/config/functions.sh -s bash'
	# python flake tests
	poetry run flake8 --statistics -j auto --count kiwi
	poetry run flake8 --statistics -j auto --count test/unit
	poetry run flake8 --statistics -j auto --count test/scripts

test: setup
	# python static code checks
	poetry run mypy kiwi
	# unit tests
	poetry run bash -c 'pushd test/unit && pytest -n 5 \
		--doctest-modules --no-cov-on-fail --cov=kiwi \
		--cov-report=term-missing --cov-fail-under=100 \
		--cov-config .coveragerc'

build: clean check test
	# build the sdist source tarball
	poetry build --format=sdist
	# provide rpm source tarball
	mv dist/kiwi-${version}.tar.gz dist/python-kiwi.tar.gz
	# update rpm changelog using reference file
	helper/update_changelog.py --since package/python-kiwi.changes --fix > \
		dist/python-kiwi.changes
	helper/update_changelog.py --file package/python-kiwi.changes >> \
		dist/python-kiwi.changes
	# update package version in spec file
	cat package/python-kiwi-spec-template | sed -e s'@%%VERSION@${version}@' \
		> dist/python-kiwi.spec
	# update package version in PKGBUILD file
	md5sums=$$(md5sum dist/python-kiwi.tar.gz | cut -d" " -f1); \
	cat package/python-kiwi-pkgbuild-template | sed \
		-e s'@%%VERSION@${version}@' \
		-e s"@%%MD5SUM@$${md5sums}@" > dist/PKGBUILD
	# provide rpm rpmlintrc
	cp package/python-kiwi-rpmlintrc dist
	# provide patches
	cp package/*.patch dist

prepare_for_pypi: clean setup
	# documentation render and tests
	poetry run make -C doc man
	# sdist tarball, the actual publishing happens via the
	# ci-publish-to-pypi.yml github action
	poetry build --format=sdist

prepare_for_docs: clean setup
	# documentation man pages
	poetry run make -C doc man
	# documentation github pages, the actual publishing via
	# the ci-publish-pages.yml github action
	poetry run bash -c 'pushd doc && \
		travis-sphinx --outdir build_gh_pages build --nowarn --source ./source'
	bash -c 'touch ./doc/build_gh_pages/.nojekyll'

clean: clean_git_attributes
	rm -rf dist
	rm -rf doc/build
	rm -rf doc/dist
