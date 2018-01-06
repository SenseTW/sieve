
PYTHON_VERSION=3

.PHONY: all init-project install update lock freeze test profile

all: init-project install

init-project:
	pipenv --python $(PYTHON_VERSION)

install:
	pipenv install
	make freeze

update:
	pipenv update
	make freeze

lock:
	pipenv lock
	make freeze

freeze:
	pipenv run pip freeze > requirements.txt

test:
	python -m unittest tests/*.py
	# py.test
