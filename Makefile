
reify: env/bin/pip reify.py build.py Makefile
	rm -rf build
	mkdir build
	env/bin/pip install . -t build
	rm -rf build/*-info build/__pycache__ build/*/__pycache__
	rm build/markupsafe/_speedups*
	mv build/reify.py build/__main__.py
	env/bin/python build.py

env/bin/pip:
	virtualenv env --python python3
	env/bin/pip install -U pip
	env/bin/pip install -e .

env/bin/py.test:
	env/bin/pip install pytest

clean:
	rm -rf build env dist reify reify.uncompressed *.egg-info __pycache__

test: unittest functional

unittest: env/bin/pip env/bin/py.test
	env/bin/py.test tests.py

functional: reify
	./functional-tests.sh

debug-functional:
	REIFY="env/bin/python reify.py" ./functional-tests.sh
