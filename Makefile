all: venv/install  ## [default] Set up local environment

venv: ## Create virtualenv
	python3 -m venv venv

venv/install: venv requirements.txt ## Install packages in venv.
	./venv/bin/pip3 install -r requirements.txt
	touch venv/install

.PHONY: run
run:  ## Run the app (in development mode)
	./venv/bin/python3 ./dash.py

.PHONY: run-prod
run-prod: ## Run the app in prod mode
	./venv/bin/waitress-serve --call dash:get_app

.PHONY: clean
clean: ## Clean up local environment.
	rm -rf venv
