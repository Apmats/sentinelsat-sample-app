from pydantic import BaseSettings


class Settings(BaseSettings):
    database_url: str = ""
    sentinelsat_user: str = ""
    sentinelsat_pass: str = ""
    image_directory: str = ""
    temp_image_directory: str = ""


settings = Settings()


def update_settings(**kwargs):
    global settings
    settings = Settings(**kwargs)


def get_settings():
    return settings
