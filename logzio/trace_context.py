import re

from opentelemetry.instrumentation.logging import LoggingInstrumentor

logzio_region_suffix = ''


def add_trace_url_field(span, record):
    if span and span.is_recording():
        # span stores the trace id as decimal, when in reality the trace id is in hex.
        # We need to convert the trace id from dec to hex to get a correct url.
        trace_id_hex = f'{span.context.trace_id:x}'
        record.trace_url = generate_app_url(trace_id_hex)


def generate_app_url(trace_id):
    return f'https://app{logzio_region_suffix}.logz.io/#/dashboard/jaeger/trace/{trace_id}'


class TraceContext:
    def __init__(self, url):
        global logzio_region_suffix
        self.region_suffix = ''
        self.get_region_suffix_from_url(url)
        logzio_region_suffix = self.region_suffix
        LoggingInstrumentor().instrument(set_logging_format=True, log_hook=add_trace_url_field)

    def get_region_suffix_from_url(self, url):
        regex = r'-\w{2}'
        match_obj = re.search(regex, url)
        if match_obj:
            self.region_suffix = match_obj.group(0)
