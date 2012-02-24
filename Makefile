PYTHON = python3

help:
	@echo targets:
	@echo '    doctest'
	@echo '    sdist'
	@echo '    user_install'
	@echo '    commit.txt'
	@echo '    commit'
	@echo '    xclip'
	@echo '    making_cakes.png'
	@echo '    pypi'
	@echo '    README.rst'
	@echo '    freecode'
	@echo '    sign'

doctest:
	$(PYTHON) -m doctest README

sdist:
	$(PYTHON) setup.py sdist --force-manifest --formats=zip

user_install:
	$(PYTHON) setup.py install --user

commit.txt: Makefile making_cakes.py README setup.py stepsim.py
	# single line because bzr diff returns false when there are diffs
	#
	bzr diff > commit.txt ; nano commit.txt

commit:
	@echo RETURN to commit using commit.txt, CTRL-C to cancel:
	@read DUMMY
	bzr commit --file commit.txt && rm -vf commit.txt

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

freecode:
	@echo RETURN to submit to freecode.com using freecode-submit.txt, CTRL-C to cancel:
	@read DUMMY
	freecode-submit < freecode-submit.txt

sign:
	rm -vf dist/*.asc
	for i in dist/*.zip ; do gpg --sign --armor --detach $$i ; done
	gpg --verify --multifile dist/*.asc
