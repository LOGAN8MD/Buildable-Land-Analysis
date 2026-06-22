from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Buildable Land Analysis"
    APP_NAME: str = "Buildable Land Analysis"
    APP_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Buffers (configurable without code change)
    DEFAULT_WETLAND_BUFFER: float = 50.0
    DEFAULT_BUILDING_BUFFER: float = 20.0
    DEFAULT_FLOOD_BUFFER: float = 0.0
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

settings = Settings()
