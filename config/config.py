import os
import zipfile
from google.cloud import storage
from google.oauth2.service_account import Credentials
import oracledb
from sqlalchemy import create_engine

def create_db_engine():
    STORAGE_NAME = os.environ.get('STORAGE_NAME')
    WALLET_FILE = os.environ.get('WALLET_FILE')

    test = {
        "type": os.environ.get('GCP_TYPE'),
        "project_id": os.environ.get('GCP_PROJECT_ID'),
        "private_key_id": os.environ.get('GCP_PRIVATE_KEY_ID'),
        "private_key": os.environ.get('GCP_PRIVATE_KEY').replace('\\n', '\n'),
        "client_email": os.environ.get('GCP_CLIENT_EMAIL'),
        "client_id": os.environ.get('GCP_CLIENT_ID'),
        "auth_uri": os.environ.get('GCP_AUTH_URI'),
        "token_uri": os.environ.get('GCP_TOKEN_URI'),
        "auth_provider_x509_cert_url": os.environ.get('GCP_PROVIDER_URL'),
        "client_x509_cert_url": os.environ.get('GCP_CLIENT_URL'),
        "universe_domain": os.environ.get('GCP_UNIV_DOMAIN')
    }

    credentials = Credentials.from_service_account_info(test)
    client = storage.Client(credentials=credentials)
    bucket = client.get_bucket(STORAGE_NAME)
    blob = bucket.get_blob(WALLET_FILE)
    blob.download_to_filename(WALLET_FILE)

    zip_file_path = os.path.join(os.getcwd(), WALLET_FILE)
    wallet_location = os.path.join(os.getcwd(), 'key')
    os.makedirs(wallet_location, exist_ok=True)

    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(wallet_location)

    connection = oracledb.connect(
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        dsn=os.environ.get('DB_DSN'),
        config_dir=wallet_location,
        wallet_location=wallet_location,
        wallet_password=os.environ.get('DB_WALLET_PASSWORD'))

    engine = create_engine('oracle+oracledb://', creator=lambda: connection)

    return engine


telegramConfig = {
    '주식 급등일보🚀급등테마·대장주 탐색기': 'https://t.me/s/FastStockNews'
    , '핀터 - 국내공시 6줄 요약': 'https://t.me/s/finter_gpt'
    , 'AWAKE-일정, 테마, 이벤트드리븐': 'https://t.me/s/awake_schedule'
    , '52주 신고가 모니터링': 'https://t.me/s/awake_realtimeCheck'
    , 'SB 리포트 요약': 'https://t.me/s/stonereport'

}