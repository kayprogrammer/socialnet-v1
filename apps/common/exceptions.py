from http import HTTPStatus
from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    AuthenticationFailed,
    ValidationError,
    APIException,
    NotFound,
)

from .responses import CustomResponse
from .error import ErrorCode


class RequestError(APIException):
    default_detail = "An error occured"

    def __init__(
        self, err_msg: str, err_code: str, status_code: int = 400, data: dict = None
    ) -> None:
        self.status_code = HTTPStatus(status_code)
        self.err_code = err_code
        self.err_msg = err_msg
        self.data = data

        super().__init__()


def custom_exception_handler(exc, context):
    try:
        response = exception_handler(exc, context)
        if isinstance(exc, AuthenticationFailed):
            exc_list = str(exc).split("DETAIL: ")
            return CustomResponse.error(
                message=exc_list[-1],
                status_code=401,
                err_code=ErrorCode.UNAUTHORIZED_USER,
            )
        elif isinstance(exc, RequestError):
            return CustomResponse.error(
                message=exc.err_msg,
                data=exc.data,
                status_code=exc.status_code,
                err_code=exc.err_code,
            )
        elif isinstance(exc, ValidationError):
            errors = exc.detail
            for key in errors:
                err_val = str(errors[key][0]).replace('"', "")
                errors[key] = err_val
                if isinstance(err_val, list):
                    errors[key] = err_val

            return CustomResponse.error(
                message="Invalid Entry",
                data=errors,
                status_code=422,
                err_code=ErrorCode.INVALID_ENTRY,
            )
        elif isinstance(exc, NotFound) and exc.detail == "Invalid page.":
            return CustomResponse.error(
                message="Invalid page",
                status_code=response.status_code,
                err_code=ErrorCode.INVALID_PAGE,
            )
        else:
            return CustomResponse.error(
                message=exc.detail if hasattr(exc, "detail") else str(exc),
                status_code=response.status_code
                if hasattr(response, "status_code")
                else 500,
                err_code=ErrorCode.SERVER_ERROR,
            )
    except APIException as e:
        print("Server Error: ", e)
        return CustomResponse.error(
            message="Server Error", status_code=500, err_code=ErrorCode.SERVER_ERROR
        )
