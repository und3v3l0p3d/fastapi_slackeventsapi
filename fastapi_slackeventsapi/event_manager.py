import asyncio
from time import time
from typing import Union, Optional, Callable, Any, Awaitable, Type
import hashlib
import hmac
import platform
import sys
import functools
import inspect

from fastapi import FastAPI, APIRouter, Header, Response, Request
from fastapi.responses import JSONResponse
from fastapi.types import DecoratedCallable

from .event_dispatcher import EventDispatcher

# Version Set as slackeventsapi
__version__ = "2.2.1"


class SlackEventManager:
    __name = 'slackeventsapi'

    def __init__(self, singing_secret: str, endpoint: str, app: Optional[Union[FastAPI, APIRouter]] = None):
        self.singing_secret = singing_secret
        self.endpoint = endpoint
        self.package_info = self.get_package_info()
        self._event_dispatcher = EventDispatcher()
        self._exception_dispatcher = EventDispatcher()
        self.app = FastAPI()
        self.__init_routes()
        if app is not None:
            self.init(app)

    def init(self, app: Union[FastAPI, APIRouter]):
        if not isinstance(app, FastAPI) and not isinstance(app, APIRouter):
            raise
        app.mount(self.endpoint, self.app, self.__name)

    @staticmethod
    def get_package_info() -> str:
        """
        This method copy of the same as slackeventsapi
        Returns:
            package_info
        """
        client_name = __name__.split('.')[0]
        client_version = __version__  # Version is returned from version.py

        # Collect the package info, Python version and OS version.
        package_info = {
            "client": "{0}/{1}".format(client_name, client_version),
            "python": "Python/{v.major}.{v.minor}.{v.micro}".format(v=sys.version_info),
            "system": "{0}/{1}".format(platform.system(), platform.release())
        }

        # Concatenate and format the user-agent string to be passed into request headers
        ua_string = []
        for key, val in package_info.items():
            ua_string.append(val)

        return " ".join(ua_string)

    def verify_signature(self, body: bytes, timestamp: int, signature: bytes):
        req = str.encode('v0:{}:'.format(timestamp)) + body
        request_hash = 'v0=' + hmac.new(
            str.encode(self.singing_secret),
            req,
            hashlib.sha256
        ).hexdigest()
        if len(request_hash) != len(signature):
            return False
        result = 0
        if isinstance(request_hash, bytes) and isinstance(signature, bytes):
            for x, y in zip(request_hash, signature):
                result |= x ^ y
        else:
            for x, y in zip(request_hash, signature):
                result |= ord(x) ^ ord(y)
        return result == 0

    # req_timestamp: Optional[int] = Header(None, alias='x-slack-request-timestamp'),
    # req_signature: Optional[bytes] = Header(None, alias='x-slack-signature'), ):
    async def __event(self,
                      request: Request, ):
        req_timestamp = request.headers.get('x-slack-request-timestamp')
        req_signature = request.headers.get('x-slack-signature')
        if request.method == 'GET':
            return Response("These are not the slackbots you're looking for.", status_code=404)
        if req_timestamp is None or abs(time() - int(req_timestamp)) > 60 * 5:
            # TODO: call here error event dispatch
            return Response("", status_code=403)
        body = await request.body()
        if req_signature is None or not self.verify_signature(body, req_timestamp, req_signature):
            # TODO: call here error event dispatch
            return Response("", status_code=403)

        event_data = await request.json()
        if "challenge" in event_data:
            return JSONResponse(content=event_data.get('challenge'), status_code=200)

        if "event" in event_data:
            event_type = event_data['event']['type']
            await self._event_dispatcher.dispatch(event_type, event_data)
            return Response(
                "",
                status_code=200,
                headers={
                    'X-Slack-Powered-By': self.package_info
                }
            )

    def __init_routes(self):
        self.app.add_route('/', route=self.__event, methods=['GET', 'POST'])

    def on_event(self, event_name: str, handler: Callable[[Any], Awaitable[Any]]):
        self._event_dispatcher.add(event_name,
                                   self._exception_event_handler(event_name, handler))

    def on(self, event_name: str) -> Callable[[DecoratedCallable], DecoratedCallable]:
        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            self.on_event(event_name, func)
            return func

        return decorator

    def add_exception(self, event_name: Union[str, Exception,], handler: Callable[[Any], Awaitable[Any]]):
        if isinstance(event_name, Exception):
            name = event_name.__class__.__name__
        elif type(event_name) == type(Exception) and issubclass(event_name, Exception):
            name = event_name().__class__.__name__
        else:
            name = event_name
        self._exception_dispatcher.add(name, self._continius_exception_handler(handler))

    def on_exception(self, event_name: Union[str, Exception]) -> Callable[[DecoratedCallable], DecoratedCallable]:
        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            self.add_exception(event_name, func)
            return func

        return decorator

    @staticmethod
    def _continius_exception_handler(func):
        async def inner(*args, **kwargs):
            try:
                _spec = inspect.getfullargspec(func)
                if not _spec.args and not _spec.varargs:
                    args = ()
                if not _spec.kwonlyargs and not _spec.varkw and not _spec.kwonlydefaults:
                    kwargs = {}
                return await func(*args, **kwargs)
            except Exception as exc:
                # TODO: add logger output here
                pass

        return inner

    def _exception_event_handler(self, event_name: str, func):
        async def inner(*args, **kwargs):
            try:
                _spec = inspect.getfullargspec(func)
                if not _spec.args and not _spec.varargs:
                    args = ()
                if not _spec.kwonlyargs and not _spec.varkw and not _spec.kwonlydefaults:
                    kwargs = {}
                return await func(*args, **kwargs)
            except Exception as exc:
                if exc.__class__.__name__ in self._exception_dispatcher:
                    await self._exception_dispatcher.dispatch(exc.__class__.__name__, exc)
                if event_name in self._exception_dispatcher:
                    await self._exception_dispatcher.dispatch(event_name, exc)

        return inner
