#!/usr/bin/make

# Disable implicit rules
.SUFFIXES:

########################################################

# Makefile for Juicer
#
# useful targets:
#   make sdist ---------------- produce a tarball
#   make rpm  ----------------- produce RPMs
#   make docs ----------------- rebuild the manpages (results are checked in)
#   make pyflakes, make pep8 -- source code checks
#   make test ----------------- run all unit tests (export LOG=true for /tmp/ logging)
#        -> testjuiceradmin; testjuicer; testrepodefs
#   make tag ------------------- tag this release with make tag TAG=FOO (usually a version-release)
########################################################

# > VARIABLE = value
#
# Normal setting of a variable - values within it are recursively
# expanded when the variable is USED, not when it's declared.
#
# > VARIABLE := value
#
# Setting of a variable with simple expansion of the values inside -
# values within it are expanded at DECLARATION time.

########################################################

# variable section
NAME := juicer

# This doesn't evaluate until it's called. The -D argument is the
# directory of the target file ($@), kinda like `dirname`.
ASCII2MAN = a2x -D $(dir $@) -d manpage -f manpage $<
ASCII2HTMLMAN = a2x -D docs/html/man/ -d manpage -f xhtml
MANPAGES := docs/man/man1/juicer.1 docs/man/man1/juicer-admin.1 docs/man/man5/juicer.conf.5

# VERSION file provides one place to update the software version.
VERSION := $(shell cat VERSION)
GITVERSION := $(shell git reflog -1 | awk '{print $$1}')
# All of these targets are rebuilt when the VERSION file is updated.
juicer/__init__.py juicer.spec setup.py: VERSION

# RPM build parameters.
RPMSPECDIR := .
RPMSPEC := $(RPMSPECDIR)/juicer.spec
RPMVERSION := $(VERSION)
RPMRELEASE = $(shell awk '/Release/{print $$2; exit}' < $(RPMSPEC).in | cut -d "%" -f1)
RPMDIST = $(shell rpm --eval '%dist')
NVR = $(RPMVERSION)-$(RPMRELEASE)$(RPMDIST)
RPMNVR = $(NAME)-$(NVR)

# Testing parameters.
LOG ?= false

########################################################

all: rpm

# To force a rebuild of the docs run 'touch VERSION && make docs'
docs: $(MANPAGES)

# Regenerate %.1.asciidoc if %.1.asciidoc.in has been modified more
# recently than %.1.asciidoc.
%.1.asciidoc: %.1.asciidoc.in VERSION
	sed "s/%VERSION%/$(VERSION)/" $< > $@

# Regenerate %.1 if %.1.asciidoc or VERSION has been modified more
# recently than %.1. (Implicitly runs the %.1.asciidoc recipe)
%.1: %.1.asciidoc
	$(ASCII2MAN)

# Regenerate %.5.asciidoc if %.5.asciidoc.in has been modified more
# recently than %.5.asciidoc.
%.5.asciidoc: %.5.asciidoc.in VERSION
	sed "s/%VERSION%/$(VERSION)/" $< > $@

# Regenerate %.5 if %.5.asciidoc or VERSION has been modified more
# recently than %.5. (Implicitly runs the %.5.asciidoc recipe)
%.5: %.5.asciidoc
	$(ASCII2MAN)

# Build the spec file on the fly. Substitute version numbers from the
# canonical VERSION file.
juicer.spec: juicer.spec.in
	sed "s/%VERSION%/$(VERSION)/" $< > $@

# Build the distutils setup file on the fly.
setup.py: setup.py.in
	sed "s/%VERSION%/$(VERSION)/" $< > $@

juicer/__init__.py: juicer/__init__.py.in
	sed "s/%VERSION%/$(VERSION)-$(GITVERSION)/" $< > $@

pep8:
	@echo "#############################################"
	@echo "# Running PEP8 Compliance Tests"
	@echo "#############################################"
# --ignore=E501,E221,W291,W391,E302,E251,E203,W293,E231,E303,E201,E225,E261
	pep8 --exclude=texttable.py --ignore=E501,E502,E123,E126,E127,E128 -r juicer/ bin/

pyflakes:
	@echo "#############################################"
	@echo "# Running Pyflakes Sanity Tests"
	@echo "#############################################"
	-pyflakes juicer/
	pyflakes bin/

clean:
	@echo "Cleaning up distutils stuff"
	@rm -rf build dist MANIFEST
	@echo "Cleaning up byte compiled python stuff"
	@find . -type f -regex ".*\.py[co]$$" -delete
	@echo "Cleaning up editor backup files"
	@find . -type f \( -name "*~" -or -name "#*" \) -delete
	@find . -type f \( -name "*.swp" \) -delete
	@echo "Cleaning up asciidoc to man transformations and results"
	@find ./docs/man -type f -name "*.xml" -delete
	@find ./docs/man -type f -name "*.asciidoc" -delete
	@echo "Cleaning up RPM building stuff"
	@rm -rf MANIFEST rpm-build

cleaner: clean
	@echo "Cleaning up harder"
	@rm -f setup.py juicer.spec

python:
	python setup.py build

install: setup.py
	python setup.py install
	mkdir -p /usr/share/man/{man1,man5}
	cp -v docs/man/man1/*.1 /usr/share/man/man1/
	cp -v docs/man/man5/*.5 /usr/share/man/man5/
	mkdir -p /usr/share/juicer
	cp -v share/juicer/juicer.conf /usr/share/juicer/
	cp -vr share/juicer/completions /usr/share/juicer/

sdist: clean
	python setup.py sdist -t MANIFEST.in

rpmcommon: juicer/__init__.py juicer.spec setup.py sdist docs
	@mkdir -p rpm-build
	@cp dist/*.gz rpm-build/

srpm: rpmcommon
	@rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir $(RPMSPECDIR)" \
	--define "_sourcedir %{_topdir}" \
	-bs $(RPMSPEC)
	@echo "#############################################"
	@echo "Juicer SRPM is built:"
	@find rpm-build -maxdepth 2 -name 'juicer*src.rpm' | awk '{print "    " $$1}'
	@echo "#############################################"

rpm: rpmcommon
	@rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir $(RPMSPECDIR)" \
	--define "_sourcedir %{_topdir}" \
	-ba $(RPMSPEC)
	@echo "#############################################"
	@echo "Juicer RPMs are built:"
	@find rpm-build -maxdepth 2 -name 'juicer*.rpm' | awk '{print "    " $$1}'
	@echo "#############################################"

# This makes an RPM for Openshift Online
oorpm: rpmcommon
	@rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir $(RPMSPECDIR)" \
	--define "_sourcedir %{_topdir}" \
	--dbpath ~/app-root/data/rpmdb/ \
	-ba $(RPMSPEC)
	@echo "#############################################"
	@echo "Juicer RPMs are built:"
	@find rpm-build -maxdepth 2 -name 'juicer*.rpm' | awk '{print "    " $$1}'
	@echo "#############################################"

koji: srpm
	koji build --scratch f17 rpm-build/$(RPMNVR).src.rpm

tag:
	git tag -s -m $(TAG) $(NAME)-$(TAG)

test: testrepodefs testjuicer testjuiceradmin
	:

testjuiceradmin:
	@if [ "$(LOG)" = "true" ]; then \
		./hacking/test_juicer_admin 2>&1 | tee -a /tmp/juicer_tests.log; \
		echo "Test results logged to /tmp/juicer_tests.log"; \
	else \
		./hacking/test_juicer_admin; \
	fi

testjuicer:
	@if [ "$(LOG)" = "true" ]; then \
		./hacking/test_juicer 2>&1 | tee -a /tmp/juicer_tests.log; \
		echo "Test results logged to /tmp/juicer_tests.log"; \
	else \
		./hacking/test_juicer; \
	fi

testrepodefs:
	@if [ "$(LOG)" = "true" ]; then \
		./hacking/test_repo_defs 2>&1 | tee -a /tmp/juicer_tests.log; \
		echo "Test results logged to /tmp/juicer_tests.log"; \
	else \
		./hacking/test_repo_defs; \
	fi

rpminstall: rpm
	-rpm -e juicer juicer-common juicer-admin
	yum localinstall rpm-build/noarch/juicer*$(NVR).noarch.rpm
