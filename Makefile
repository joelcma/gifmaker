APP_NAME := gifmaker
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
DIST_DIR := dist
BINARY := $(DIST_DIR)/$(APP_NAME)
INSTALL_PATH := /usr/local/bin/$(APP_NAME)
EXECUTABLE ?= $(INSTALL_PATH)
RELEASE_DIR := release
ARCH := $(shell uname -m)
OS := $(shell uname -s | tr '[:upper:]' '[:lower:]')
RELEASE_NAME := $(APP_NAME)-$(OS)-$(ARCH)
RELEASE_PATH := $(RELEASE_DIR)/$(RELEASE_NAME)

.PHONY: help venv install-deps run build release deploy install-context-menu uninstall-context-menu full_install clean

help:
	@echo "Targets:"
	@echo "  venv         Create local virtual environment"
	@echo "  install-deps Install Python dependencies + PyInstaller"
	@echo "  run          Run app with project virtual environment"
	@echo "  build        Build one-file binary in $(DIST_DIR)/"
	@echo "  release      Create tar.gz release bundle in $(RELEASE_DIR)/"
	@echo "  deploy       Build and install binary to $(INSTALL_PATH)"
	@echo "  install-context-menu   Install desktop/context menu integration"
	@echo "  uninstall-context-menu Remove desktop/context menu integration"
	@echo "  full_install Build, deploy, and install context menu integration"
	@echo "  clean        Remove build artifacts"

venv:
	python3 -m venv $(VENV)

install-deps: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt pyinstaller

run: install-deps
	$(PYTHON) app.py

build: install-deps
	$(PYTHON) -m PyInstaller --noconfirm --onefile --name $(APP_NAME) app.py

release: build
	rm -rf "$(RELEASE_PATH)" "$(RELEASE_PATH).tar.gz"
	mkdir -p "$(RELEASE_PATH)"
	cp "$(BINARY)" "$(RELEASE_PATH)/$(APP_NAME)"
	cp README.md "$(RELEASE_PATH)/README.md"
	cp scripts/install_context_menu.sh "$(RELEASE_PATH)/install_context_menu.sh"
	cp scripts/uninstall_context_menu.sh "$(RELEASE_PATH)/uninstall_context_menu.sh"
	chmod +x "$(RELEASE_PATH)/$(APP_NAME)" "$(RELEASE_PATH)/install_context_menu.sh" "$(RELEASE_PATH)/uninstall_context_menu.sh"
	tar -czf "$(RELEASE_PATH).tar.gz" -C "$(RELEASE_DIR)" "$(RELEASE_NAME)"
	@echo "Release bundle created: $(RELEASE_PATH).tar.gz"

deploy: build
	./scripts/deploy.sh "$(BINARY)" "$(INSTALL_PATH)"

install-context-menu:
	./scripts/install_context_menu.sh "$(EXECUTABLE)"

uninstall-context-menu:
	./scripts/uninstall_context_menu.sh

full_install:
	$(MAKE) install-deps
	$(MAKE) deploy
	$(MAKE) install-context-menu

clean:
	rm -rf build dist *.spec __pycache__ gifmaker_app/__pycache__
