# Digital Cashbook

Business hub staff facing site for Prisoner Money suite of apps.

## Running locally

It's recommended that you use a python virtual environment to isolate each application.
Please call this `venv` and make sure it's in the root folder of this application so that
`mtp_common.test_utils.code_style.CodeStyleTestCase` and the build tasks can find it.

In order to run the application locally, it is necessary to have the API running.
Please refer to the [money-to-prisoners-api](https://github.com/ministryofjustice/money-to-prisoners-api/) repository.

Once the API has started locally, run

```
./run.py serve
# or
./run.py start
```

This will build everything and run the local server at [http://localhost:8001](http://localhost:8001).

You should be able to login using following credentials: `test-prison-1` or `test-prison-2`

### Alternative: Docker

In order to run a server that's exactly similar to the production machines,
you need to have [Docker](https://www.docker.com/products/developer-tools) installed. Run

```
./run.py local_docker
```

and you should be able to connect to the local server.

## Developing

[![CircleCI](https://circleci.com/gh/ministryofjustice/money-to-prisoners-cashbook.svg?style=svg)](https://circleci.com/gh/ministryofjustice/money-to-prisoners-cashbook)

With the `./run.py` command, you can run a browser-sync server, and get the assets
to automatically recompile when changes are made, run `./run.py serve` instead of
`./run.py start`. The server is then available at the URL indicated.

```
./run.py test
```

Runs all the application tests.

You can connect a local version of [money-to-prisoners-common](https://github.com/ministryofjustice/money-to-prisoners-common/)
for development by pre-pending the following task to the run script.

```
python_dependencies --common-path [path]
```

### Translating

Update translation files with `./run.py make_messages` – you need to do this every time any translatable text is updated.

Pull updates from Transifex with `./run.py translations --pull`.
You'll need to update translation files afterwards and manually check that the merges occurred correctly.

Push latest English to Transifex with `./run.py translations --push`.
NB: you should pull updates before pushing to merge correctly.

## Deploying

This is handled by [money-to-prisoners-deploy](https://github.com/ministryofjustice/money-to-prisoners-deploy/).
