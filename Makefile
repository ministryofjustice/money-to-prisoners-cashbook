ERROR=\033[0;31m   # Red
WARNING=\033[0;33m # Yellow
RESET=\033[0m
err=echo "$(ERROR)$(1)$(RESET)"
warn=echo "$(WARNING)$(1)$(RESET)"

all: lint test run

lint: build
	docker-compose run django bash -c \
	    "pip install --quiet -r requirements/dev.txt && \
	     flake8 ."

test: build
	$(API_ENDPOINT) docker-compose run django bash -c \
	    "pip install --quiet -r requirements/dev.txt && \
	     /app/manage.py test $(TEST)"

run: build
	$(API_ENDPOINT) docker-compose up

build: .dev_django_container

ifneq ($(shell command -v boot2docker),)
  API_ENDPOINT=API_URL=http://`boot2docker ip`:8000

  b2d_status=$(shell boot2docker status)

  ifneq ($(b2d_status),running)
    boot2docker_up=boot2docker_up
    boot2docker_up:
	    boot2docker init
	    boot2docker up
  endif

  ifndef DOCKER_HOST
    boot2docker_shellinit=boot2docker_shellinit
    boot2docker_shellinit: $(boot2docker_up)
	    @$(call warn,Setting boot2docker environment variables)
	    @$(call warn,Run this to avoid doing setting them every time:)
	    @$(call warn,$$ eval "\$$\(boot2docker shellinit\)")
	    $(foreach line, $(shell boot2docker shellinit), $(eval $(line)))
  endif
endif

.dev_django_container: Dockerfile docker-compose.yml \
  requirements/base.txt requirements/prod.txt \
  | $(boot2docker_up) $(boot2docker_shellinit)
	docker-compose build
	@docker inspect -f '{{.Id}}' moneytoprisonerscashbook_django > .dev_django_container

clean:
	@rm -f .dev_django_container
	docker-compose stop
	docker-compose rm -f

.PHONY: all lint test run build boot2docker_up boot2docker_shellinit clean
