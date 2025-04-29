from pydantic import BaseModel,field_validator


class chat_request_schema(BaseModel):
    message: str
    access_token: str
    userid:str
@field_validator("access_token")
def validate_access_token(cls, v):
    if v in " ":
        raise ValueError("space not allowed")
    if v == "":
        raise ValueError("empty string not allowed")
    if v == None:
        raise ValueError("None not allowed")
    return v
    
class chat_response_schema(BaseModel):
    message:str