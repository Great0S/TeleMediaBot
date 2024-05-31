from logging import config as Config
import logging
import os
from deep_translator import GoogleTranslator
from pydantic_settings import BaseSettings
from config.logger import log_config

# Declaring global variables
class Settings(BaseSettings):
    
    # Alert to telegram channel info
    alert_session: str = "kids_alert"
    alert_channel_id: int = os.getenv('ALERTCHANNELID')
    alert_bot_token: str = os.getenv('ALERTBOTTOKEN')
    alert_bot_user: str = os.getenv('ALERTBOTUSER')
    
    # Logger config
    Config.dictConfig(log_config)
    logger: logging.Logger = logging.getLogger("mainLog")
    logs_dir: str = "logs/"
    
    # Translation
    turk_translate: GoogleTranslator = GoogleTranslator(source="tr", target="en")
    english_translate: GoogleTranslator = GoogleTranslator(source="en", target="ar")
    arabic_translate: GoogleTranslator = GoogleTranslator(source="ar", target="en")

    # Telegram API Config
    api_id: int = os.getenv('BFAPIID')
    api_hash: str = os.getenv('BFAPIHASH')
    alert_api_id: int = os.getenv('ALERTCHANNELID')
    alert_api_hash: str = os.getenv('ALERTAPIHASH')

    # Telegram BOT info
    username: str = os.getenv('BFUSERNAME')
    phone: int = os.getenv('PHONE')
    token: str = os.getenv('BFBOTTOKEN')
    bot_id: str = os.getenv('BFBOTID')
    session_name: str = "kids_tele_bot"

    # Telegram Channels info
    kids_id: list = [os.getenv('KIDSCHANNEL1'), os.getenv('KIDSCHANNEL2')]

    # Server Config
    Target: str = "https://7e5e-213-254-138-110.eu.ngrok.io"

    # Ecwid info    
    category_id: int = 127443595

    # Ecwid connection info
    products_url: str = "https://app.ecwid.com/api/v3/63690252/products"
    category_url: str = "https://app.ecwid.com/api/v3/63690252/categories"
    ecwid_token: str = f"?token={os.getenv('ECWIDTOKEN')}"
    payload: dict = {}
    ecwid_headers: dict = {
    "Authorization": f"Bearer {os.getenv('ECWIDTOKEN')}",
    "Content-Type": "application/json;charset: utf-8"
    }

    class Config:
        case_sensitive = True

class BaseConfig():
   API_PREFIX = "/api"
   TESTING = False
   DEBUG = False


class DevConfig(BaseConfig):
   FLASK_ENV = "development"
   DEBUG = True
   SQLALCHEMY_DATABASE_URI = "postgresql://db_user:db_password@db-postgres:5432/flask-deploy"
   CELERY_BROKER = "pyamqp://rabbit_user:rabbit_password@broker-rabbitmq//"
   CELERY_RESULT_BACKEND = "rpc://rabbit_user:rabbit_password@broker-rabbitmq//"


class ProductionConfig(BaseConfig):
   FLASK_ENV = "production"
   SQLALCHEMY_DATABASE_URI = "postgresql://db_user:db_password@db-postgres:5432/flask-deploy"
   CELERY_BROKER = "pyamqp://rabbit_user:rabbit_password@broker-rabbitmq//"
   CELERY_RESULT_BACKEND = "rpc://rabbit_user:rabbit_password@broker-rabbitmq//"


class TestConfig(BaseConfig):
   FLASK_ENV = "development"
   TESTING = True
   DEBUG = True
   # make celery execute tasks synchronously in the same process
   CELERY_ALWAYS_EAGER = True



settings = Settings()