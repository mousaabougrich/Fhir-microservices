from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "FHIR De-Identification Service"
    admin_email: str = "admin@example.com"
    items_per_page: int = 10
    database_url: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/deid",
        env="DATABASE_URL",
    )
    fhir_proxy_base_url: str = Field(
        default="http://localhost:8080",
        env="FHIR_PROXY_BASE_URL",
    )

    # Pydantic v2 settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()