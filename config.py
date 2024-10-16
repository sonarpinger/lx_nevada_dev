from pydantic import SecretStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DEBUG: bool = False
    SECRET_KEY: SecretStr
    PVE_HOST: str
    PVE_USER: str
    PVE_PASSWORD: SecretStr
    OIDC_METADATA_URL: str
    OIDC_CLIENT_ID: str
    OIDC_CLIENT_SECRET: SecretStr
    OIDC_REDIRECT_URL: str
    OIDC_SCOPE: str
    OIDC_LOGOUT_URL: str
    BASE_URL: str
    LDAP_SERVER: str
    LDAP_PORT: str
    LDAP_BIND_DN: str
    LDAP_BIND_PASSWORD: SecretStr
    LDAP_COMMON_AUTH_BASE: str
    LDAP_ADMIN_AUTH_BASE: str
    LDAP_PROFESSOR_AUTH_BASE: str
    LDAP_USER_SEARCH_BASE: str
    LDAP_COMPUTER_SEARCH_BASE: str
    LDAP_SEARCH_ATTRIBUTE: str
    LDAP_DOMAIN: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
