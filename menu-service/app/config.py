from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://byteorder:byteorder@postgres:5432/byteorder"
    otel_endpoint: str = ""
    otel_service_name: str = "menu-service"

    class Config:
        env_file = ".env"


settings = Settings()
