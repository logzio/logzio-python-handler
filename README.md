# Logz.io python handler
Python handler that sends logs in bulk over https to logz.io. The handler use an internal buffer, and you can choose the drain timeout, and the number of messages to hold in queue before drain. Everything is working in threads, and they would exit after completing draining all the logs if the main program exits.

**This is BETA. We currently use this handler internally. We will provide tests soon.**

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
TBD