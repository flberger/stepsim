PYTHON = python3

help:
	@echo targets: doctest, sdist, user_install, commit.txt, commit

doctest:
	$(PYTHON) -m doctest README

sdist:
	$(PYTHON) setup.py sdist --force-manifest --formats=zip

user_install:
	$(PYTHON) setup.py install --user

commit.txt: Makefile making_cakes.py README setup.py stepsim.py
	bzr diff >> commit.txt

commit:
	@echo RETURN to commit using commit.txt, CTRL-C to cancel:
	@read DUMMY
	bzr commit --file commit.txt && echo > commit.txt
