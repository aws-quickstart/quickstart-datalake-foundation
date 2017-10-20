import traceback
import functools
import logging


logger = logging.getLogger(__name__)


class QuickstartException(Exception):
    """Base class for exceptions raised by API methods in Quickstart
    Makes easier to handle exceptions in webapp
    """

    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


def compose_error_payload(exception):
    tb = traceback.format_exc()
    error_payload = {
        'exception': exception.__class__.__name__,
        'description': str(exception),
        'traceback': tb
    }
    return error_payload


class PublishTopicException(Exception):
    pass


class AthenaQueryError(Exception):
    pass


def handle_quickstart_exception(error_message):

    def outer(fun):
        @functools.wraps(fun)
        def inner(*args, **kwargs):
            try:
                response = fun(*args, **kwargs)
            except Exception as e:
                payload = compose_error_payload(e)
                logger.exception("%s:\n%s", error_message, payload['traceback'])
                raise QuickstartException(error_message, payload=payload)
            return response

        return inner

    return outer
