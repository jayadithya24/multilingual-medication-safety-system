"""Keep query parameters (including speech text) out of HTTP access logs."""
import logging


class AccessPathFilter(logging.Filter):
    def filter(self, record):
        if isinstance(record.args, tuple) and len(record.args) == 5:
            args = list(record.args)
            args[2] = str(args[2]).split('?', 1)[0]
            record.args = tuple(args)
        return True


def configure():
    logger = logging.getLogger('uvicorn.access')
    if not any(isinstance(item, AccessPathFilter) for item in logger.filters):
        logger.addFilter(AccessPathFilter())
