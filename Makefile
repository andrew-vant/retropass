.PHONY : all wheel venv clean test

all : sdist wheel
wheel :
	python3 setup.py bdist_wheel

sdist :
	python3 setup.py sdist

upload-test:
	twine upload -r test dist/*

upload: all
	twine upload dist/*

test :
	pytest-3 --cov src

cov :
	pytest-3 --cov src --cov-report term-missing

clean :
	-rm -rf build dist venv src/*.egg-info .tox
