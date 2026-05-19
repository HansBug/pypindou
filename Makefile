.PHONY: help resource package build clean test unittest docs pdocs rst_auto docs_auto todos_auto tests_auto

PYTHON ?= $(if $(wildcard ./venv/bin/python),./venv/bin/python,$(shell which python))
PYTHON_ABS := $(if $(wildcard $(PYTHON)),$(abspath $(PYTHON)),$(PYTHON))

PROJ_DIR := .
DOC_DIR  := ${PROJ_DIR}/docs
DIST_DIR := ${PROJ_DIR}/dist
TEST_DIR := ${PROJ_DIR}/test
SRC_DIR  := ${PROJ_DIR}/pypindou

RANGE_DIR      ?= .
RANGE_TEST_DIR := ${TEST_DIR}/${RANGE_DIR}
RANGE_SRC_DIR  := ${SRC_DIR}/${RANGE_DIR}
RANGE_SRC_DIR_TEST := ${TEST_DIR}/${RANGE_DIR}

COV_TYPES ?= xml term-missing
AUTO_OPTIONS ?= --param max_tokens=400000 --no-ignore-module pypindou --model-name gpt-5.2-codex

PYTHON_CODE_DIR   := ${SRC_DIR}
RST_DOC_DIR       := ${DOC_DIR}/source/api_doc
PYTHON_CODE_FILES := $(shell find ${PYTHON_CODE_DIR} -name "*.py" ! -name "__*.py" 2>/dev/null)
RST_DOC_FILES     := $(patsubst ${PYTHON_CODE_DIR}/%.py,${RST_DOC_DIR}/%.rst,${PYTHON_CODE_FILES})
PYTHON_NONM_FILES := $(shell find ${PYTHON_CODE_DIR} -name "__init__.py" 2>/dev/null)
RST_NONM_FILES    := $(foreach file,${PYTHON_NONM_FILES},$(patsubst %/__init__.py,%/index.rst,$(patsubst ${PYTHON_CODE_DIR}/%,${RST_DOC_DIR}/%,$(patsubst ${PYTHON_CODE_DIR}/__init__.py,${RST_DOC_DIR}/index.rst,${file}))))

help:
	@echo "pypindou Build System"
	@echo "======================"
	@echo "  make resource   - Build packaged palette resources from submodules"
	@echo "  make package    - Build sdist and wheel"
	@echo "  make test       - Run pytest unit tests"
	@echo "  make docs       - Build Sphinx docs"
	@echo "  make rst_auto   - Generate API RST files"
	@echo "  make clean      - Remove build artifacts"

resource:
	$(PYTHON) -m tools.build_resource -p ${PROJ_DIR} -o ${SRC_DIR}/resources/palettes.json

package: resource
	$(PYTHON) -m build --sdist --wheel --outdir ${DIST_DIR}

build: package

clean:
	rm -rf ${DIST_DIR} build *.egg-info coverage.xml junit.xml
	rm -rf ${DOC_DIR}/build

test: unittest

unittest: resource
	UNITTEST=1 \
		$(PYTHON) -m pytest "${RANGE_TEST_DIR}" \
		-sv -m unittest \
		--junitxml=junit.xml -o junit_family=legacy \
		$(shell for type in ${COV_TYPES}; do echo "--cov-report=$$type"; done) \
		--cov="${RANGE_SRC_DIR}" \
		$(if ${MIN_COVERAGE},--cov-fail-under=${MIN_COVERAGE},) \
		$(if ${WORKERS},-n ${WORKERS},)

docs: rst_auto
	$(MAKE) -C "${DOC_DIR}" build PYTHON="$(PYTHON_ABS)"

pdocs:
	$(MAKE) -C "${DOC_DIR}" prod

docs_auto:
	$(PYTHON) -m hbllmutils code pydoc -i "${RANGE_SRC_DIR}" ${AUTO_OPTIONS}

todos_auto:
	$(PYTHON) -m hbllmutils code todo -i "${RANGE_SRC_DIR}" ${AUTO_OPTIONS}

tests_auto:
	$(PYTHON) -m hbllmutils code unittest -i "${RANGE_SRC_DIR}" -o "${RANGE_SRC_DIR_TEST}" ${AUTO_OPTIONS}

rst_auto: ${RST_DOC_FILES} ${RST_NONM_FILES} auto_rst_top_index.py
	$(PYTHON) auto_rst_top_index.py -i ${PYTHON_CODE_DIR} -o ${DOC_DIR}/source

${RST_DOC_DIR}/%.rst: ${PYTHON_CODE_DIR}/%.py auto_rst.py Makefile
	@mkdir -p $(dir $@)
	$(PYTHON) auto_rst.py -i $< -o $@

${RST_DOC_DIR}/%/index.rst: ${PYTHON_CODE_DIR}/%/__init__.py auto_rst.py Makefile
	@mkdir -p $(dir $@)
	$(PYTHON) auto_rst.py -i $< -o $@

${RST_DOC_DIR}/index.rst: ${PYTHON_CODE_DIR}/__init__.py auto_rst.py Makefile
	@mkdir -p $(dir $@)
	$(PYTHON) auto_rst.py -i $< -o $@
