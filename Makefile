test:
	pytest --cov=gptman

coverage:
	coverage json
	coverage xml
