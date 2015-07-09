ifneq ($(shell command -v boot2docker),)
API_ENDPOINT=API_URL=http://`boot2docker ip`:8000
endif

run: build
	$(API_ENDPOINT) docker-compose up

build: .dev_django_container

.dev_django_container: .
	docker-compose build
	@docker inspect -f '{{.Id}}' moneytoprisonerscashbook_django > .dev_django_container

clean:
	@rm -f .dev_django_container
	docker-compose stop
	docker-compose rm -f

.PHONY: run build clean
