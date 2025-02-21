from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework.exceptions import ValidationError
from apps.common.error import ErrorCode
import json


class BaseConsumer(AsyncWebsocketConsumer):
    async def validate_entry(self, entry_data, serializer_class):
        err = None
        try:
            data_json = json.loads(entry_data)
            serializer = serializer_class(data=data_json)
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            err = await self.err_handler(e)

        if err:
            return err, False
        return serializer.data, True

    async def err_handler(self, exc):
        err = {}
        if isinstance(exc, json.decoder.JSONDecodeError) or exc.detail.get(
            "non_field_errors"
        ):
            err["type"] = ErrorCode.INVALID_DATA_TYPE
            err["message"] = "Data is not a valid json"

        elif isinstance(exc, ValidationError):
            errors = exc.detail
            for key in errors:
                err_val = str(errors[key][0]).replace('"', "")
                errors[key] = err_val
                if isinstance(err_val, list):
                    errors[key] = err_val

            err["type"] = ErrorCode.INVALID_ENTRY
            err["message"] = "Invalid entry data"
            err["data"] = errors
        return err

    async def send_error_message(self, error):
        err = {"status": "error"} | error
        # Send an error message to the client
        await self.send(json.dumps(err))
