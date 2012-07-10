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
# All of these targets are rebuilt when the VERSION file is updated.
juicer/__init__.py juicer.spec setup.py: VERSION

# RPM build parameters.
RPMSPECDIR := .
RPMSPEC := $(RPMSPECDIR)/juicer.spec
RPMVERSION := $(VERSION)
RPMRELEASE = $(shell awk '/Release/{print $$2; exit}' < $(RPMSPEC).in | cut -d "%" -f1)
RPMDIST = $(shell rpm --eval '%dist')
RPMNVR = $(NAME)-$(RPMVERSION)-$(RPMRELEASE)$(RPMDIST)

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
	sed "s/%VERSION%/$(VERSION)/" $< > $@

pep8:
	@echo "#############################################"
	@echo "# Running PEP8 Compliance Tests"
	@echo "#############################################"
# --ignore=E501,E221,W291,W391,E302,E251,E203,W293,E231,E303,E201,E225,E261
	pep8 -r juicer/ bin/

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
	@rm -f setup.py juicer.spec juicer/__init__.py

python:
	python setup.py build

install:
	python setup.py install

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
	@echo "    rpm-build/$(RPMNVR).src.rpm"
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
	@echo "Juicer RPM is built:"
	@echo "    rpm-build/noarch/$(RPMNVR).noarch.rpm"
	@echo "#############################################"

koji: srpm
	koji build --scratch f17 rpm-build/$(RPMNVR).src.rpm

test:
	. ./hacking/setup-env
	if [ "$(LOG)" = "true" ]; then \
		./hacking/tests | tee /tmp/juicer_tests.log; \
	else \
		./hacking/tests; \
	fi

rpminstall: rpm
	rpm -e juicer
	rpm -Uvh rpm-build/noarch/$(RPMNVR).noarch.rpm
