# Monitoring microservices*
*docker compose solution is quite buggy because it lacks synchronization between containers, app could be run as follows
```
docker-compose up -d rabbit
docker-compose up -d pg
python backend/web_service.py
python backend/message_db.py
python backend/crawler_service.py
```
```
backend/web_service.py - web service for task management + REST api + monitoring data display
backend/crawler_service.py - rabbitmq based service, yields tasks from db via rabbitmq and from rabbitmq queu
backend/message_logger.py - logs messages from ampq to file
backend/message_db.py - makes SQL request to the db based on rabbitmq messages and returns results
```



![Alt text](/website_monitoring.png?raw=true "Optional Title")

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
