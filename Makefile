.PHONY: build clean rebuild

build:
	pyinstaller build.spec

clean:
	rm -rf build dist __pycache__ *.pyc

rebuild: clean build

install:
	pip install .

dev:
	pip install -e . --group dev
	ln -s $(HOME)/.local/state/staticgallerybuilder logs

lint:
	ruff check .

format:
	ruff format .

fix:
	ruff check . --fix