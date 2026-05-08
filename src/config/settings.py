from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Classe responsável por guardar as informações de segurança para o Projeto."""

    APP_KEY: str
    APP_SECRET: str
    BASE_URL: str
    
    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )