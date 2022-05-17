.PHONY: test

test:
	mkdir -p reports/
	pytest --cov=rj --junitxml=reports/pytest.xml || true
	pylint --exit-zero --disable=R,C --output-format=parseable --reports=y ./rj > reports/pylint.log
