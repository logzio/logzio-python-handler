[![PyPI version](https://badge.fury.io/py/logzio-python-handler.svg)](https://badge.fury.io/py/logzio-python-handler) [![Build Status](https://travis-ci.org/logzio/logzio-python-handler.svg?branch=master)](https://travis-ci.org/logzio/logzio-python-handler)

# The Logz.io Python Handler

<table><tr><th>

### Deprecation announcement

Version 3.0.0 of this project ends support for Python 2.7, 3.3, and 3.4. We recommend migrating your projects to Python 3.5 or newer as soon as possible. We'll be happy to answer any questions you have in [a GitHub issue](https://github.com/logzio/logzio-python-handler/issues).

Thanks! <br>
The Logz.io Integrations team

</th></tr></table>

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

## Tested Python Versions
Travis CI will build this handler and test against:
  - "3.5"
  - "3.6"
  - "3.7"
  - "3.8"
  - "3.9"

We can't ensure compatibility to any other version, as we can't test it automatically.

To run tests:

```bash
$ pip install tox
$ tox
...

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
 - Backup logs flag. Set to False, will disable the local backup of logs in case of failure. (defaults to "True")
 - Network timeout, in seconds, int or float, for sending the logs to logz.io. (defaults to 10)
 - Retries number (retry_no, defaults to 4).
 - Retry timeout (retry_timeout) in seconds (defaults to 2).

 Please note, that you have to configure those parameters by this exact order.
 i.e. you cannot set Debug to true, without configuring all of the previous parameters as well.

#### Dict Config
```
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'logzioFormat': {
            'format': '{"additional_field": "value"}',
            'validate': False
        }
    },
    'handlers': {
        'logzio': {
            'class': 'logzio.handler.LogzioHandler',
            'level': 'INFO',
            'formatter': 'logzioFormat',
            'token': '<<LOGZIO-TOKEN>>',
            'logzio_type': 'python-handler',
            'logs_drain_timeout': 5,
            'url': 'https://<<LOGZIO-URL>>:8071',
            'retries_no': 4,
            'retry_timeout': 2,
        }
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['logzio'],
            'propagate': True
        }
    }
}
```
Replace:
* <<LOGZIO-TOKEN>> - your logz.io account token.
* <<LOGZIO-URL>> - logz.io url, as described [here](https://docs.logz.io/user-guide/accounts/account-region.html#regions-and-urls).
#### Serverless platforms

If you're using a serverless function, you'll need to import and add the LogzioFlusher annotation before your sender function. To do this, in the code sample below, uncomment the `import` statement and the `@LogzioFlusher(logger)` annotation line.  
**Note:** For the LogzioFlusher to work properly, you'll need to make sure that the Logz.io. handler is added to the root logger. See the configuration above for an example.

#### Code Example
```python
import logging
import logging.config
# If you're using a serverless function, uncomment.
# from logzio.flusher import LogzioFlusher

# Say I have saved my dictionary configuration in a variable named 'LOGGING' - see 'Dict Config' sample section
logging.config.dictConfig(LOGGING)
logger = logging.getLogger('superAwesomeLogzioLogger')

# If you're using a serverless function, uncomment.
# @LogzioFlusher(logger)
def my_func():
    logger.info('Test log')
    logger.warn('Warning')

    try:
        1/0
    except:
        logger.exception("Supporting exceptions too!")
```

#### Extra Fields
In case you need to dynamic metadata to your logger, other then the constant metadata from the formatter, you can use the "extra" parameter.
All key values in the dictionary passed in "extra" will be presented in Logz.io as new fields in the log you are sending.
Please note, that you cannot override default fields by the python logger (i.e. lineno, thread, etc..)
For example:


```
logger.info('Warning', extra={'extra_key':'extra_value'})
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
            'debug': True,
            'network_timeout': 10,
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
- logzio_type - Log type, for searching in logz.io (defaults to "python"), it cannot contain a space.
- appname - Your django app

## Trace context

If you're sending traces with OpenTelemetry instrumentation (auto or manual), you can correlate your logs with the trace context.
That way, your logs will have traces data in it, such as service name, span id and trace id.
To enable this feature, set the `add_context` param in your handler configuration to `True`, like in this example:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'logzioFormat': {
            'format': '{"additional_field": "value"}',
            'validate': False
        }
    },
    'handlers': {
        'logzio': {
            'class': 'logzio.handler.LogzioHandler',
            'level': 'INFO',
            'formatter': 'logzioFormat',
            'token': '<<LOGZIO-TOKEN>>',
            'logzio_type': 'python-handler',
            'logs_drain_timeout': 5,
            'url': 'https://<<LOGZIO-URL>>:8071',
            'retries_no': 4,
            'retry_timeout': 2,
            'add_context': True
        }
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['logzio'],
            'propagate': True
        }
    }
}
```

Please note that if you are using `python 3.8`, it is preferred to use the `logging.config.dictConfig` method, as mentioned in [python's documentation](https://docs.python.org/3/library/logging.config.html#configuration-file-format).

## Release Notes
- 4.0.1
  - Updated `protobuf>=3.20.2`.
  - Added dependency `setuptools>=65.5.1`
  
- 4.0.0
  - Add ability to automatically attach trace context to the logs.

- 3.1.1
  - Bug fixes (issue #68, exception message formatting)
  - Added CI: Tests and Auto release 

<details>
  <summary markdown="span"> Expand to check old versions </summary>

- 3.1.0
    - Bug fixes
    - Retry number and timeout is now configurable
    
- 3.0.0
    - Deprecated `python2.7` & `python3.4`
    - Changed log levels on `_flush_queue()` method (@hilsenrat)

- 2.0.15
    - Added flusher decorator for serverless platforms(@mcmasty)
    - Add support for `python3.7` and `python3.8` 

- 2.0.13 
    - Add support for `pypy` and `pypy3`(@rudaporto-olx)
    - Add timeout for requests.post() (@oseemann) 
- 2.0.12 - Support disable logs local backup
- 2.0.11 - Completely isolate exception from the message
- 2.0.10 - Not ignoring formatting on exceptions
- 2.0.9 - Support extra fields on exceptions too (Thanks @asafc64!)
- 2.0.8 - Various PEP8, testings and logging changes (Thanks @nir0s!)
- 2.0.7 - Make sure sending thread is alive after fork (Thanks @jo-tham!)
- 2.0.6 - Add "flush()" method to manually drain the queue (Thanks @orenmazor!)
- 2.0.5 - Support for extra fields
- 2.0.4 - Publish package as source along wheel, and supprt python3 packagin (Thanks @cchristous!)
- 2.0.3 - Fix bug that consumed more logs while draining than Logz.io's bulk limit
- 2.0.2 - Support for formatted messages (Thanks @johnraz!)
- 2.0.1 - Added __all__ to __init__.py, so support * imports
- 2.0.0 - Production, stable release.
    - *BREAKING* - Configuration option logs_drain_count was removed, and the order of the parameters has changed for better simplicity. Please review the parameters section above.
    - Introducing the LogzioSender class, which is generic and can be used without the handler wrap to ship raw data to Logz.io. Just create a new instance of the class, and use the append() method.
    - Simplifications and Robustness
    - Full testing framework
- 1.X - Beta versions
  

</details>
