from fastapi.exceptions import RequestValidationError,  ResponseValidationError
from fastapi import Request,Response,status

async def validation_exception_handler(request:Request, exc:RequestValidationError):
    
    error = exc.errors()
    error_messages = []
    field = error.get("loc", [])[-1] if error.get("loc") else "unknown"
    error_messages.append({
            "field": field,
            "message": f"Field '{field}' is required" if error.get("type") == "missing" else error.get("msg")
        })
    return Response(content=error_messages, status_code=status.HTTP_404_NOT_FOUND)

