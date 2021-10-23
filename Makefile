.PHONY: all
all: venv/install  ## [default] Set up local environment

venv: ## Create virtualenv
	python3 -m venv venv

venv/install: venv requirements.txt ## Install packages in venv.
	./venv/bin/pip3 install -r requirements.txt
	touch venv/install

.PHONY: run
run: venv/install ## Run the app (in development mode)
	FLASK_APP=run.py FLASK_ENV=dev FLASK_DEBUG=1 ./venv/bin/python3 -m flask run --host=0.0.0.0 --port=5000

.PHONY: run-prod
run-prod: venv/install ## Run the app in prod mode
	./venv/bin/waitress-serve --host=0.0.0.0 --port=5000 --call run:get_app

.PHONY: docker
docker: ## Build a docker image
	sudo docker build --tag michaelkelly.org/weatherdash:latest .

.PHONY: docker-run
docker-run: ## Run the latest docker image
	sudo docker run --name weatherdash -ti --rm -p 5000:8080 michaelkelly.org/weatherdash:latest

.PHONY: clean
clean: ## Clean up local environment.
	rm -rf venv

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
