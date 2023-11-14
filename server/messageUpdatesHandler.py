import asyncio
import json
from .baseHandler import BaseHandler
from robot import History

class MessageUpdatesHandler(BaseHandler):
    """Long-polling request for new messages.

    Waits until new messages are available before returning anything.
    """

    async def post(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            cursor = self.get_argument("cursor", None)
            history = History.History()
            messages = history.get_messages_since(cursor)
            while not messages:
                # Save the Future returned here so we can cancel it in
                # on_connection_close.
                self.wait_future = history.cond.wait(timeout=1)
                try:
                    await self.wait_future
                except asyncio.CancelledError:
                    return
                messages = history.get_messages_since(cursor)
            if self.request.connection.stream.closed():
                return
            res = {"code": 0, "message": "ok", "history": json.dumps(messages)}
            self.write(json.dumps(res))
        self.finish()

    def on_connection_close(self):
        self.wait_future.cancel()