SHELL = /bin/sh
PYTHON = /usr/bin/python3.5
PYLINT = /usr/bin/pylint3

SOURCE = recfile.py test_recfile.py

.PHONY: all lint pep8 test clean spotless

all: lint

lint:
	$(PYLINT) $(SOURCE)
pep8:
	$(PYTHON) -mpep8 --max-line-length=70 $(SOURCE)
test:
	$(PYTHON) -m unittest discover
clean:
	rm -rf __pycache__ recfile.pyc
	cd testdata && rm -f *.out
spotless: clean
