***REMOVED***
***REMOVED***
***REMOVED***
from pydantic import BaseSettings
***REMOVED***

***REMOVED***
***REMOVED***
    
***REMOVED***
    alert_session = 'kids_alert'
    alert_channel_id = -1001834749560
    alert_bot_token = '5860981689:AAGBF84N0n7rBPNz9TX_ZtB9bdvpyd4Vdbw'
    alert_bot_user = 'bf_bots_info'
    
***REMOVED***
***REMOVED***
    logger = logging.getLogger('mainLog')
    logs_dir: str = 'logs/'
    
***REMOVED***
    turk_translate = GoogleTranslator(source='tr', target='en')
    english_translate = GoogleTranslator(source='en', target='ar')
    arabic_translate = GoogleTranslator(source='ar', target='en')

***REMOVED***
    api_id: int = 7148663
    api_hash: str = '81c16de88cd5e25fcbf01e5af332b41f'
    alert_api_id: int = 9859004
    alert_api_hash: str = '9c813daded173c825a1ca2e618063089'

***REMOVED***
    username: str = 'albeyanfashion2'
    phone: int = 905434050709
    token: str = '5606280453:AAHKKi33s_F-H5Cymh0aAT25dEatHKPJYDc'
    bot_id: str = '@CocukStoreBot'
    session_name: str = 'kids_tele_bot'

***REMOVED***
    kids_id = [-1001338146588, -1001653408221]

***REMOVED***
    Target: str = 'https://7e5e-213-254-138-110.eu.ngrok.io'

***REMOVED***
***REMOVED***

***REMOVED***
    products_url = "https://app.ecwid.com/api/v3/63690252/products"
    category_url = "https://app.ecwid.com/api/v3/63690252/categories"
    ecwid_token = "?token=secret_4i936SRqRp3317MZ51Aa4tVjeUVyGwW7"
    payload = {}
    ecwid_headers = {
    "Authorization": "Bearer secret_4i936SRqRp3317MZ51Aa4tVjeUVyGwW7",
    "Content-Type": 'application/json;charset: utf-8'
***REMOVED***

***REMOVED***
***REMOVED***

***REMOVED***
   API_PREFIX = '/api'
***REMOVED***
***REMOVED***


***REMOVED***
   FLASK_ENV = 'development'
***REMOVED***
   SQLALCHEMY_DATABASE_URI = 'postgresql://db_user:db_password@db-postgres:5432/flask-deploy'
   CELERY_BROKER = 'pyamqp://rabbit_user:rabbit_password@broker-rabbitmq//'
   CELERY_RESULT_BACKEND = 'rpc://rabbit_user:rabbit_password@broker-rabbitmq//'


***REMOVED***
   FLASK_ENV = 'production'
   SQLALCHEMY_DATABASE_URI = 'postgresql://db_user:db_password@db-postgres:5432/flask-deploy'
   CELERY_BROKER = 'pyamqp://rabbit_user:rabbit_password@broker-rabbitmq//'
   CELERY_RESULT_BACKEND = 'rpc://rabbit_user:rabbit_password@broker-rabbitmq//'


***REMOVED***
   FLASK_ENV = 'development'
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***



***REMOVED***