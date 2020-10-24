all: venv/install  ## [default] Set up local environment

venv: ## Create virtualenv
	python3 -m venv venv

venv/install: venv requirements.txt ## Install packages in venv.
	./venv/bin/pip3 install -r requirements.txt
	touch venv/install

.PHONY: run
run:  ## Run the app (in development mode)
	FLASK_APP=dash.py FLASK_ENV=dev FLASK_DEBUG=1 ./venv/bin/python3 -m flask run --host=0.0.0.0 --port=5001

.PHONY: run-prod
run-prod: ## Run the app in prod mode
	./venv/bin/waitress-serve --host=0.0.0.0 --port=5000 --call dash:get_app 

.PHONY: clean
clean: ## Clean up local environment.
	rm -rf venv
