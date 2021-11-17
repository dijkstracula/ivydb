SRC_ROOT=ivydb/

check: check-venv
	mypy ${SRC_ROOT}

check-venv:
ifndef VIRTUAL_ENV
	$(error No Python virtualenv found; \
	see README.md for setup and activation details; \
	likely need to run "source <VIRTUAL_ENV_DIR>/bin/activate")
endif
