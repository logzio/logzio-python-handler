[![PyPI version](https://badge.fury.io/py/logzio-python-handler.svg)](https://badge.fury.io/py/logzio-python-handler) [![Build Status](https://travis-ci.org/logzio/logzio-python-handler.svg?branch=master)](https://travis-ci.org/logzio/logzio-python-handler)

# The Logz.io Python Handler
This is a Python handler that sends logs in bulk over HTTPS to Logz.io.  
The handler uses a subclass named LogzioSender (which can be used without this handler as well, to ship raw data).  
The LogzioSender class opens a new Thread, that consumes from the logs queue. Each iteration (its frequency of which can be configured by the logs_drain_timeout parameter), will try to consume the queue in its entirety.  
Logs will get divided into separate bulks, based on their size.  
LogzioSender will check if the main thread is alive. In case the main thread quits, it will try to consume the queue one last time, and then exit. So your program can hang for a few seconds, until the logs are drained.  
In case the logs failed to be sent to Logz.io after a couple of tries, they will be written to the local file system. You can later upload them to Logz.io using curl.

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
formatter=logzioFormat
args=('token', 'my_type')

[formatters]
keys=logzioFormat

[loggers]
keys=root

[logger_root]
handlers=LogzioHandler
level=INFO

[formatter_logzioFormat]
format={"additional_field": "value"}
```
*args=() arguments, by order*
 - Your logz.io token
 - Log type, for searching in logz.io (defaults to "python")
 - Time to sleep between draining attempts (defaults to "3")
 - Logz.io Listener address (defaults to "https://listener.logz.io:8071")
 - Debug flag. Set to True, will print debug messages to stdout. (defaults to "False")
 
 Please note, that you have to configure those parameters by this exact order.  
 i.e. you cannot set Debug to true, without configuring all of the previous parameters as well.

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
        'logzioFormat': {
            'format': '{"additional_field": "value"}'
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
            'formatter': 'logzioFormat',
            'token': 'token',
            'logzio_type': "django",
            'logs_drain_timeout': 5,
            'url': 'https://listener.logz.io:8071',
            'debug': True
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
- url - Logz.io Listener address
- logs_drain_count - Number of logs to keep in buffer before draining
- logs_drain_timeout - Time to wait before draining, regardless of the previouse setting
- logzio_type - Log type, for searching in logz.io (defaults to "python")
- appname - Your django app

## Release Notes
- 2.0.0 - Production, stable release. 
    - *BREAKING* - Configuration option logs_drain_count was removed, and the order of the parameters has changed for better simplicity. Please review the parameters section above.
    - Introducing the LogzioSender class, which is generic and can be used without the handler wrap to ship raw data to Logz.io. Just create a new instance of the class, and use the append() method.
    - Simplifications and Robustness
    - Full testing framework
- 1.X - Beta versions