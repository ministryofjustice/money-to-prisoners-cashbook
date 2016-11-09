# Money to Prisoners Cashbook


The Cashbook UI for the Money to Prisoners Project


## Running locally


In order to run the application locally, it is necessary to have the API running.
Please refer to the [money-to-prisoners-api](https://github.com/ministryofjustice/money-to-prisoners-api/) repository.

Once the API is running locally, run

```
make start
```

This will build everything (which will initially take a while) and run
the local server at [http://localhost:8001](http://localhost:8001).

### Alternative: Docker

In order to run a server that's exactly similar to the production machines,
you need to have [Docker](https://www.docker.com/docker-toolbox) installed. Run

```
make docker
```

and you should eventually be able to connect to the local server.

### Log in to the application

You should be able to log into the cash book app using following credentials:

- *test-prison-1 / test-prison-1* for Prison 1
- *test-prison-2 / test-prison-2* for Prison 2

## Developing

With the `make` command, you can run a browser-sync server, and get the assets
to automatically recompile when changes are made, run `make serve` instead of
`make start`. The server is then available at the URL indicated.

```
make test
```

Runs all the application tests.

### Translating

Update translation files with `cd mtp_cashbook; ../manage.py makemessages --all --keep-pot --no-wrap`.

Pull updates from Transifex with `tx pull`. You'll need to update translation files afterwards.

Push latest English to Transifex with `tx push -s`. NB: always pull updates before pushing to merge correctly.

## Deploying

This is handled by MOJ Digital's CI server. Request access and head there. Consult the dev
runbook if necessary.
