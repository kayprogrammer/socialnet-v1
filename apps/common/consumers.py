from channels.generic.websocket import AsyncWebsocketConsumer
import json


class BaseConsumer(AsyncWebsocketConsumer):
    async def validate_entry(self, value):
        err = {}
        try:
            text_data_json = json.loads(value)
            message = text_data_json
            if not isinstance(message, dict):
                err["type"] = "invalid_data_type"
                err["message"] = "Data is not a valid json"
            elif not message:
                err["type"] = "invalid_data"
                err["message"] = "Data is empty"
        except:
            err["type"] = "invalid_data_type"
            err["message"] = "Data is not a valid json"
        if err:
            return err, False
        return message, True

    async def send_error_message(self, error):
        err = {"status": "error"} | error
        # Send an error message to the client
        await self.send(json.dumps(err))
