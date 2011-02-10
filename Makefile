PYTHON = python3

help:
	@echo targets: doctest, sdist, user_install, commit.txt, commit, xclip, making_cakes.png, pypi

doctest:
	$(PYTHON) -m doctest README

sdist:
	$(PYTHON) setup.py sdist --force-manifest --formats=zip

user_install:
	$(PYTHON) setup.py install --user

commit.txt: Makefile making_cakes.py README setup.py stepsim.py
	bzr diff > commit.txt

commit:
	@echo RETURN to commit using commit.txt, CTRL-C to cancel:
	@read DUMMY
	bzr commit --file commit.txt && echo > commit.txt

xclip:
	pandoc --strict README | xclip

making_cakes.png: making_cakes.dot
	dot -Tpng making_cakes.dot > making_cakes.png && xv making_cakes.png

making_cakes.dot: stepsim.py making_cakes.py
	python3 making_cakes.py

pypi:
	$(PYTHON) setup.py register

README.rst: README
	pandoc --output README.rst README
