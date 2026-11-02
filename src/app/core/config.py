from pydantic_settings import BaseSettings,SettingsConfigDict
from functools import lru_cache

class setting(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "industrial-ai-service"
    APP_ENV: str = "development"
    APP_LOG_LEVEL: str = "INFO"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Modbus 配置
    MODBUS_HOST: str = "localhost"
    MODBUS_PORT: int = 5020
    MODBUS_SLAVE_ID: int = 1
    MODBUS_TIMEOUT: float = 3.0

    #OPC UA 配置
    OPCUA_HOST: str = "localhost"
    OPCUA_PORT: int = 4840
    OPCUA_NS_URI: str = "http://my.factory.namespace"

    #MQTT 配置
    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_TOPIC_PREFIX: str = "factory"

@lru_cache()
def get_settings() -> setting:
    return setting()