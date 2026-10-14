from pydantic_settings import BaseSettings,SettingsConfigDict
from functools import lru_cache

class setting(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    APP_NAME: str = "industrial-ai-service"
    APP_ENV: str = "development"
    APP_LOG_LEVEL: str = "INFO"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    MODBUS_HOST: str = "localhost"
    MODBUS_PORT: int = 502
    MODBUS_SLAVE_ID: int = 1
    MODBUS_TIMEOUT: float = 3.0

    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_TOPIC_PREFIX: str = "factory"

@lru_cache()
def get_settings() -> setting:
    return setting()