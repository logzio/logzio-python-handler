# Logz.io Python Handler

[![PyPI version](https://badge.fury.io/py/logzio-python-handler.svg)](https://badge.fury.io/py/logzio-python-handler) [![Build Status](https://travis-ci.org/logzio/logzio-python-handler.svg?branch=master)](https://travis-ci.org/logzio/logzio-python-handler)

## Logz.io Python Handler setup

Logz.io Python Handler sends logs in bulk over HTTPS to Logz.io.
Logs are grouped into bulks based on their size.

If the main thread quits, the handler tries to consume the remaining logs and then exits.
If the handler can't send the remaining logs, they are written to the local file system for later retrieval.

### Add the dependency to your project

Navigate to your project's folder in the command line, and run this command to install the dependency.

```shell
pip install logzio-python-handler
```

### Configure Logz.io Python Handler for a standard Python project

Use the samples in the code block below as a starting point, and replace the sample with a configuration that matches your needs.

For a complete list of options, see the configuration parameters below the code block.👇

```python
[handlers]
keys=LogzioHandler

[handler_LogzioHandler]
class=logzio.handler.LogzioHandler
formatter=logzioFormat

# Parameters must be set in order. Replace these parameters with your configuration.
args=('<<SHIPPING-TOKEN>>', '<<LOG-TYPE>>', <<TIMEOUT>>, '<<LISTENER-HOST>>:8071', <<DEBUG-FLAG>>)

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

**Parameters**

**Important**:
Arguments must be configured in the order shown.
For example, to set debug-flag to `True`, you need to set every argument that comes before it.

| Parameter | Description |
|---|---|
| account-token | **Required**. Your Logz.io [account token](https://app.logz.io/#/dashboard/settings/general). <br>  Replace `<<SHIPPING-TOKEN>>` with the [token](https://app.logz.io/#/dashboard/settings/general) of the account you want to ship to. |
| log-type | **Default**: `python` <br>  The [log type](https://docs.logz.io/user-guide/log-shipping/built-in-log-types.html), shipped as `type` field.  Used by Logz.io for consistent parsing.  Can't contain spaces. |
| timeout | **Default**: `3` <br>  Time to wait between log draining attempts, in seconds. |
| listener-url | **Default**: `https://listener.logz.io:8071` <br>  Listener URL and port. <br>  Replace `<<LISTENER-HOST>>` with your region's listener host (for example, `listener.logz.io`). For more information on finding your account's region, see [Account region](https://docs.logz.io/user-guide/accounts/account-region.html). |
| debug-flag | **Default**: `False` <br>  Debug flag. To print debug messages to stdout, `True`. Otherwise, `False`. |

**Code sample**

```python
import logging
import logging.config

# If configuration is stored at ./myconf.conf:
logging.config.fileConfig('myconf.conf')

logger = logging.getLogger('superAwesomeLogzioLogger')

logger.info('Test log')
logger.warn('Warning')

try:
    1/0
except:
    logger.exception("Supporting exceptions too!")
```

To add dynamic metadata to your logger other than the constant metadata from the formatter, you can use the `extra` parameter.
Key-value pairs passed in `extra` are shown as new fields in Logz.io.
Please note that you can't override default fields from the python logger, such as `lineno` or `thread`.

```python
logger.info('Warning', extra={'extra_key':'extra_value'})
```

## Release Notes
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
