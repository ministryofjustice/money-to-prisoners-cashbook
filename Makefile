# app defaults
app=cashbook
port=8001
browsersync_port=3001
browsersync_ui_port=3031

NODE_MODULES := node_modules
MTP_COMMON := $(NODE_MODULES)/money-to-prisoners-common

ifeq ($(VIRTUAL_ENV),)
	PYTHON_BIN=$(shell if [ -d "venv" ]; then echo "venv/bin/"; fi)
else
	PYTHON_BIN=$(VIRTUAL_ENV)/bin/
endif

# include shared Makefile, installing it if necessary
.PHONY: install-common
install-common:
	@echo "The installation process is about to start. It usually takes a while."
	@echo "The only thing that this script doesn't do is set up the API. While"
	@echo "installation is running, head to https://github.com/ministryofjustice/money-to-prisoners-api"
	@echo "to find out how to run it."
	@$(PYTHON_BIN)pip install money-to-prisoners-common
	@$(eval export PYTHON_LIBS=$(shell $(PYTHON_BIN)python find_common.py))

$(MTP_COMMON):
	@npm install
	@npm install `cat $(PYTHON_LIBS)/mtp_common/npm_requirements.txt`
	@echo Copying mtp_common assets to node_modules
	@mkdir $(MTP_COMMON)
	@cp -R $(PYTHON_LIBS)/mtp_common/assets $(MTP_COMMON)

%: install-common $(MTP_COMMON)
	@$(MAKE) -f $(PYTHON_LIBS)/mtp_common/Makefile app=$(app) port=$(port) browsersync_port=$(browsersync_port) browsersync_ui_port=$(browsersync_ui_port) $@
