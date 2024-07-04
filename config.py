import os
import zipfile
from google.cloud import storage
from google.oauth2.service_account import Credentials
import oracledb
from sqlalchemy import create_engine
from starlette.config import Config

config = Config('../.env')

def create_db_engine():
    STORAGE_NAME = config('STORAGE_NAME')
    WALLET_FILE = config('WALLET_FILE')

    test = {
        "type": config('GCP_TYPE'),
        "project_id": config('GCP_PROJECT_ID'),
        "private_key_id": config('GCP_PRIVATE_KEY_ID'),
        "private_key": config('GCP_PRIVATE_KEY').replace('\\n', '\n'),
        "client_email": config('GCP_CLIENT_EMAIL'),
        "client_id": config('GCP_CLIENT_ID'),
        "auth_uri": config('GCP_AUTH_URI'),
        "token_uri": config('GCP_TOKEN_URI'),
        "auth_provider_x509_cert_url": config('GCP_PROVIDER_URL'),
        "client_x509_cert_url": config('GCP_CLIENT_URL'),
        "universe_domain": config('GCP_UNIV_DOMAIN')
    }

    credentials = Credentials.from_service_account_info(test)
    client = storage.Client(credentials=credentials)
    bucket = client.get_bucket(STORAGE_NAME)
    blob = bucket.get_blob(WALLET_FILE)
    blob.download_to_filename(WALLET_FILE)

    zip_file_path = os.path.join(os.getcwd(), WALLET_FILE)
    wallet_location = os.path.join(os.getcwd(), 'key')

    if not os.path.exists(wallet_location) :
        os.makedirs(wallet_location, exist_ok=True)
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(wallet_location)

    connection = oracledb.connect(
        user=config('DB_USER'),
        password=config('DB_PASSWORD'),
        dsn=config('DB_DSN'),
        config_dir=wallet_location,
        wallet_location=wallet_location,
        wallet_password=config('DB_WALLET_PASSWORD'))

    engine = create_engine('oracle+oracledb://', creator=lambda: connection)

    return engine


telegramConfig = {
    '주식 급등일보🚀급등테마·대장주 탐색기': 'https://t.me/s/FastStockNews'
    , '핀터 - 국내공시 6줄 요약': 'https://t.me/s/finter_gpt'
    , 'AWAKE-일정, 테마, 이벤트드리븐': 'https://t.me/s/awake_schedule'
    , '52주 신고가 모니터링': 'https://t.me/s/awake_realtimeCheck'
    , 'SB 리포트 요약': 'https://t.me/s/stonereport'

}