all: venv/install  ## [default] Set up local environment

venv: ## Create virtualenv
	python3 -m venv venv

venv/install: venv requirements.txt ## Install packages in venv.
	./venv/bin/pip3 install -r requirements.txt
	touch venv/install

.PHONY: run
run:  ## Run the app
	export FLASK_APP=dash.py; ./venv/bin/python -m flask run --host=0.0.0.0

.PHONY: clean
clean: ## Clean up local environment.
	rm -rf venv

