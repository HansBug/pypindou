PROJ_DIR    ?= ${CURDIR}
SPHINXOPTS  ?=
SPHINXBUILD ?= $(shell which sphinx-build)
SOURCEDIR   ?= ${PROJ_DIR}/source
BUILDDIR    ?= ${PROJ_DIR}/build

.PHONY: help build html prod clean

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

build: html

html:
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@touch "$(BUILDDIR)/html/.nojekyll"

prod: html

clean:
	@$(SPHINXBUILD) -M clean "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
