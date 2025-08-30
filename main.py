from fastapi import FastAPI, Depends
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from config import *
import requests
import pandas as pd
import pytz
from datetime import datetime, timedelta
from domain.ETF import etf_router
from domain.Stock import stock_router
from domain.Home import home_router
from domain.Market import market_router

# 1. 기본 설정값
telegram_dict = telegramConfig

# 2. 앱 생성
app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173",
    "https://etface.kr",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(etf_router.router)
app.include_router(stock_router.router)
app.include_router(home_router.router)
app.include_router(market_router.router)

app.mount("/_app", StaticFiles(directory="frontend/dist/_app"), name="_app")

@app.get("/")
def index():
    return FileResponse("frontend/dist/index.html")

# @app.get("/{full_path:path}")
# async def spa_catch_all(full_path: str):
#     return FileResponse("frontend/dist/index.html")

# @app.get("/robots.txt")
# def robots():
#     return FileResponse("frontend/dist/robots.txt")


@app.get("/codelist")
def get_code_list(db: Session = Depends(get_db)):

    try :
        data = pd.read_sql('SELECT * FROM code_list', con = db.connection())
        db.close()
        return data.reset_index(drop=True).to_json(orient='records')
    except oracledb.DatabaseError as e:
        logger.error(f'Database operation failed: {e}')

@app.get("/calendar")
def get_calendar_data():
    days_ago = 3
    days_later = 7

    tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(tz)

    start_date = (now - timedelta(days=days_ago)).strftime('%Y-%m-%d')
    end_date = (now + timedelta(days=days_later)).strftime('%Y-%m-%d')
    address = 'https://asp.zeroin.co.kr/eco/includes/wei/module/json_getData.php'
    str_nation = 'United+States|미국|China|중국|Japan|일본|South+Korea|한국|'
    str_natcd = 'us|cn|jp|kr|'
    url = f'{address}?start_date={start_date}&end_date={end_date}&str_nation={str_nation}&str_natcd={str_natcd}&str_importance=3|2|1|'

    response = requests.get(url)
    response.encoding = response.apparent_encoding
    data = pd.DataFrame(response.json())
    cols = ['nat_hname', 'date', 'time', 'kevent', 'previous', 'forecast', 'actual', 'importance_class']
    data = data[cols]

    data.columns = ['국가', '날짜', '시간', '지표명', '이전 실적', '이번 예상', '실제 실적', '중요도']

    # 2024-11-26 중요도 데이터가 바뀌어서 수정함
    data['중요도'] = data['중요도'].apply(lambda x: x.split("_")[-1])
    data['중요도'] = data['중요도'].str.replace("high", "상")
    data['중요도'] = data['중요도'].str.replace("md", "중")
    data['중요도'] = data['중요도'].str.replace("low", "하")

    # 전처리 : 엔 표기 변경
    data[['이전 실적', '이번 예상', '실제 실적']] = data[['이전 실적', '이번 예상', '실제 실적']].apply(lambda x: x.str.replace("&yen;", "￥"))

    # 데이터 정렬
    data = data.sort_values(['날짜', '시간'])

    return data.reset_index().to_json(orient='split')