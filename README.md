# Money to Prisoners Cashbook
The Cashbook UI for the Money to Prisoners Project

## Dependencies
### Docker
To run this project locally you need to have
[Docker](http://docs.docker.com/installation/mac/) and
[Docker Compose](https://docs.docker.com/compose/install/) installed.

### Other Repositories

Alongside this repository you'll need the [API
server](https://github.com/ministryofjustice/money-to-prisoners-api)
and if you're planning to deploy then you'll need the [deployment
repository](https://github.com/ministryofjustice/money-to-prisoners-deploy)
(private repository).

## Working with the code

### Run the tests

In a terminal `cd` into the directory you checked this project out into, then:

```
$ make test
```

To run a specific test, or set of tests, run:

```
$ make test TEST=[testname]
```

### Validate code style

In a terminal `cd` into the directory you checked this project out into, then:

```
$ make lint
```

To check for a [specific class of style
violation](http://flake8.readthedocs.org/en/latest/warnings.html), run:

```
$ make lint LINT_OPTS="--select [lint-rules]"
```

### Run a development Server

In a terminal `cd` into the directory you checked this project out into, then

```
$ make run
```

Wait while Docker does it's stuff and you'll soon see something like:
```
djangogulpserve_1 | [BS] Now you can access your site through the following addresses:
djangogulpserve_1 | [BS] Local URL: http://localhost:3000
```

You should be able to point your browser at
[http://localhost:3000](http://localhost:3000) if you're using
*boot2docker* then it'll be at the IP of the boot2docker virtual
machine. You can find it by typing `boot2docker ip` in a terminal. Then
visit http://**boot2docker ip**:3000/

### Log in to the application

Make sure you have a version of the [API](https://github.com/ministryofjustice/money-to-prisoners-api) server
running on port 8000.

You should be able to log into the cash book app using following credentials:

- *test_prison_1 / test_prison_1* for Prison 1
- *test_prison_2 / test_prison_2* for Prison 2
