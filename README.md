# Money to Prisoners Cashbook
The Cashbook UI for the Money to Prisoners Project

## Dependencies
### Docker
To run this project locally you need to have 
[Docker](http://docs.docker.com/installation/mac/) and 
[Docker Compose](https://docs.docker.com/compose/install/) installed.

### Other Repositories
Alongside this repository you'll need the [API server](https://github.com/ministryofjustice/money-to-prisoners-api)
and if you're planning to deploy then you'll need the [deployment repository](https://github.com/ministryofjustice/money-to-prisoners-deploy)

## Development Server
### Boot2Docker
> If you're developing on a Mac then Docker won't run natively, you'll be running 
> a single VM with linux installed where your Docker containers run. To start the vm 
> run the following first before continuing:
> ```
> $ boot2docker up
> $ eval "$(boot2docker shellinit)"
> ```

In a terminal `cd` into the directory you checked this project out into, then
```
$ docker-compose build && docker-compose up
```

Wait while Docker does it's stuff and you'll soon see something like:
```
djangogulpserve_1 | [BS] Now you can access your site through the following addresses:
djangogulpserve_1 | [BS] Local URL: http://localhost:3000
```

you should be able to point your browser at
[http://localhost:3000](http://localhost:3000)
if you're using *boot2docker* then it'll be at the IP of the boot2docker virtual machine.
You can find it by typing `boot2docker ip` in a terminal. Then visit http://**boot2docker ip**:3000/

Testing GitHub building.
