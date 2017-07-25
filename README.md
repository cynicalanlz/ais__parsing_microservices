# Monitoring microservices

## Init db

```
see db_create.sql
```


## Build dockerfile
```
docker build -f config/Dockerfile -t  ais_rabbitmq
```


## Build ampq docker
```

docker run -d --log-driver=syslog -e RABBITMQ_NODENAME=my-rabbit --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

## Launch backend
```
cd backend
pip-compile reqs.in && pip install -r reqs.in
```
