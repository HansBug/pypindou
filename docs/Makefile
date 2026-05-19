PROJ_DIR    ?= ${CURDIR}
PYTHON      ?= python
SPHINXOPTS  ?=
SPHINXBUILD ?= $(PYTHON) -m sphinx
SOURCEDIR   ?= ${PROJ_DIR}/source
BUILDDIR    ?= ${PROJ_DIR}/build

.PHONY: help build html prod clean

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

build: html

html:
	@PYTHONPATH="$(abspath ..):$${PYTHONPATH}" $(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@touch "$(BUILDDIR)/html/.nojekyll"

prod: html

clean:
	@PYTHONPATH="$(abspath ..):$${PYTHONPATH}" $(SPHINXBUILD) -M clean "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
