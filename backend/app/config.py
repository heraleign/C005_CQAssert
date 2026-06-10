from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MySQL
    mysql_host: str = "172.18.0.57"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "123456"
    mysql_db: str = "cqassert"

    # Redis
    redis_host: str = "192.168.137.189"
    redis_port: int = 6379
    redis_db: int = 0

    # App
    app_name: str = "CQAssert Backend"
    debug: bool = True
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # EOP
    eop_gateway_url: str = ""
    eop_app_key: str = ""
    eop_app_secret: str = ""

    # Search limit
    search_daily_limit: int = 20

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}"
            f"?charset=utf8mb4"
        )

    class Config:
        env_file = ".env"

settings = Settings()
