from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()  # load .env ở root

KEYCLOAK_ISSUER_URI = os.getenv("KEYCLOAK_ISSUER_URI", "").rstrip("/")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "")

JWKS_URL = f"{KEYCLOAK_ISSUER_URI}/protocol/openid-connect/certs" if KEYCLOAK_ISSUER_URI else None

PORT_KEYCLOAK = int(os.getenv("PORT_KEYCLOAK", 8080))

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "ChatBot_AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    #Server
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    #Database
    MONGODB_URI : str
    # AI_Provider
    AI_PROVIDER: str
    #OpenAI
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str
    OPENAI_MODEL: str
    #API_Settings
    REQUEST_TIMEOUT: int = 30
    # Scoring Thresholds
    GRAMMAR_WEIGHT: float = 0.3
    VOCABULARY_WEIGHT: float = 0.3
    FLUENCY_WEIGHT: float = 0.2
    NATURALNESS_WEIGHT: float = 0.2
    #CORS
    CORS_ORIGIN : list[str] = ["http://localhost:3000" or "http://localhost:5170" or "http://localhost:8000"]
    KEYCLOAK_ISSUER_URI: str = KEYCLOAK_ISSUER_URI
    KEYCLOAK_CLIENT_ID: str = KEYCLOAK_CLIENT_ID
    JWKS_URL: Optional[str] = JWKS_URL
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

@lru_cache() # @lru_cache() giúp ghi nhớ kết quả của hàm get_settings()
def get_settings() -> Settings:
    # -> Setting là trả về một instance ( đối tượng) của lớp Settings
    return Settings()

settings = get_settings()
# gọi hàm get_setting() là lưu đối tượng của lớp Settings và biến settings