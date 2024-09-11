test:
	pytest --cov=gptman

coverage:
	coverage json
	coverage xml

build:
	python -m build

release:
	twine upload dist/*
