from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    GEMINI_API_KEY:str
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: str
    DATABASE_NAME: str
    
    
    class Config:
        env_file = ".env"
        extra = "ignore"
        
    