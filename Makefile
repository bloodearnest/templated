DEPS = jinja2 pyyaml


contemplate: env/bin/pip contemplate.py build.py Makefile
	rm -rf build
	mkdir build
	env/bin/pip install $(DEPS) -t build
	rm -rf build/*-info build/*/__pycache__
	rm build/markupsafe/_speedups*
	cp contemplate.py build/__main__.py
	env/bin/python build.py
	env/bin/python -m zipapp -p "/usr/bin/env python3" build -o contemplate.raw

env/bin/pip:
	virtualenv env --python python3
	env/bin/pip install -U pip
	env/bin/pip install $(DEPS)

env/bin/py.test:
	env/bin/pip install pytest

clean:
	rm -rf build env contemplate

.PHONY: test
test: contemplate env/bin/pip env/bin/py.test
	#./tests.sh
	env/bin/py.test tests.py

debug:
	EXEC="env/bin/python contemplate.py" ./tests.sh
