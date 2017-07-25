LOGGING_FORMAT="%(name)s~%(asctime)s~%(filename)s~%(created)f~%(funcName)s~%(levelno)s~%(lineno)d~%(msecs)d~%(levelname)s~%(name)s~%(asctime)s~%(filename)s~%(created)f~%(funcName)s~%(levelno)s~%(lineno)d~%(msecs)d~%(levelname)s~%(message)s""%(name)s~%(asctime)s~%(filename)s~%(created)f~%(funcName)s~%(levelno)s~%(lineno)d~%(msecs)d~%(levelname)s~%(name)s~%(asctime)s~%(filename)s~%(created)f~%(funcName)s~%(levelno)s~%(lineno)d~%(msecs)d~%(levelname)s~%(message)s"

PG_SETTINGS={
	'user': 'aiopg',
	'database' : 'aiopg',
	'host' : '127.0.0.1',
	'password' : 'aiopg'
}

PG_DSN = 'dbname=aiopg user=aiopg password=aiopg host=127.0.0.1'


RABBIT = {
	'login' : 'rabbitmq', 
	'password' : 'rabbitmq'
	}