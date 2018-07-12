SHELL = /bin/sh
PYTHON = /usr/bin/python3.5
PYLINT = /usr/bin/pylint3

SOURCE = recfile.py test_recfile.py

lint:
	$(PYLINT) $(SOURCE)
test:
	$(PYTHON) -m unittest discover
clean:
	rm -rf __pycache__
	cd testdata && rm -f *.out
spotless: clean
