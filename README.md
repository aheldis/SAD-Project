# Mobile Fuel Delivery

# Requirements

* Install [Docker](https://docs.docker.com/engine/install/debian/) and [docker-compose](https://docs.docker.com/compose/install/) on your system


# Setup

```
cd FuelApp
sudo docker-compose up
```

if you changed requirements or dockerfile.base use `--build` flag


# Creating migrations
when your app is up with docker

```
docker-compose exec webapp python manage.py makemigrations
```
