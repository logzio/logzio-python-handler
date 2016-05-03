# The Logz.io Python Handler
This is a Python handler that sends logs in bulk over HTTPS to Logz.io. The handler uses an internal buffer, and you can choose the drain timeout as well as the number of messages to hold in the queue before the drain. Everything works in threads, so if the main program exists, the threads will continue to work until all logs are drained.

**This is in BETA. We currently use this handler internally. We will provide tests soon**

## Installation
```bash
pip install logzio-python-handler
```

## Python configuration
#### Config File
```
[handlers]
keys=LogzioHandler

[handler_LogzioHandler]
class=logzio.handler.LogzioHandler
formatter=jsonFormat
args=('token', 10, 20)

[formatters]
keys=jsonFormat

[loggers]
keys=root

[logger_root]
handlers=LogzioHandler
level=INFO

[formatter_jsonFormat]
format={ "loggerName":"%(name)s", "functionName":"%(funcName)s", "lineNo":"%(lineno)d", "levelName":"%(levelname)s", "message":"%(message)s"}
```
*args=() arguments, by order*
 - Your logz.io token
 - Number of logs to keep in buffer before draining
 - Time to wait before draining, regardless of the previouse setting
 - Log type, for searching in logz.io (defaults to "python")

#### Code Example
```python
import logging
import logging.config

# Say i have saved my configuration under ./myconf.conf
logging.config.fileConfig('myconf.conf')
logger = logging.getLogger('superAwesomeLogzioLogger')

logger.info('Test log')
logger.warn('Warning')

try:
    1/0
except:
    logger.exception("Supporting exceptions too!")
```

## Django configuration
```
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'json': {
            'format': '{ "loggerName":"%(name)s", "functionName":"%(funcName)s", "lineNo":"%(lineno)d", "levelName":"%(levelname)s", "message":"%(message)s"}'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'verbose'
        },
        'logzio': {
            'class': 'logzio.handler.LogzioHandler',
            'level': 'INFO',
            'formatter': 'json',
            'token': 'token',
            'logs_drain_count': 10,
            'logs_drain_timeout': 5,
            'logzio_type': "django"
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', ],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO')
        },
        'appname': {
            'handlers': ['console', 'logzio'],
            'level': 'INFO'
        }
    }
}

```
*Change*
- token - Your logzio token
- logs_drain_count - Number of logs to keep in buffer before draining
- logs_drain_timeout - Time to wait before draining, regardless of the previouse setting
- logzio_type - Log type, for searching in logz.io (defaults to "python")
- appname - Your django app