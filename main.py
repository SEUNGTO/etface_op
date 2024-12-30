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

# 1. 기본 설정값
telegram_dict = telegramConfig

# 2. 앱 생성
app = FastAPI()

origins = [
    "http://43.201.252.164:8000",
    "http://localhost:5173"
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

app.mount("/assets", StaticFiles(directory="frontend/dist/assets"))

@app.get("/")
def index():
    return FileResponse("frontend/dist/index.html")

@app.get("/codelist")
def get_code_list(db: Session = Depends(get_db)):

    try :
        data = pd.read_sql('SELECT * FROM code_list', con = db.connection())
        db.close()
        return data.reset_index(drop=True).to_json(orient='records')
    except oracledb.DatabaseError as e:
        logger.error(f'Database operation failed: {e}')

@app.get("/entire/new")
def get_all_new_data(db: Session = Depends(get_db)):
    try :
        q = f"""
        SELECT etf_name, stock_code, stock_name, recent_quantity, recent_amount, recent_ratio
        FROM etf_base_table
        WHERE 1 = 1 
        and recent_ratio <> 0
        and past_ratio = 0
        """
        data = pd.read_sql(q, con = db.connection())
        data['recent_quantity'] = data['recent_quantity'].apply(lambda x: f'{x:,.0f}')
        data['recent_amount'] = data['recent_amount'].apply(lambda x: f'{x :,.0f}')
        data['recent_ratio'] = data['recent_ratio'].apply(lambda x: f'{x :.2f}')
        data.columns = ['ETF', '종목코드', '종목명', '보유량', '보유금액', '비중']
        return {
            'data': data.reset_index(drop=True).to_json(orient='records')
        }
    except oracledb.DatabaseError as e:
        logger.error(f'[get_all_new_data]Database operation failed: {e}')


@app.get("/entire/drop")
def get_all_drop_data(db: Session = Depends(get_db)):
    try :
        q = f"""
        SELECT etf_name, stock_code, stock_name, past_quantity, past_amount, past_ratio
        FROM etf_base_table
        WHERE 1 = 1 
        and recent_ratio = 0
        and past_ratio <> 0
        """

        data = pd.read_sql(q, con = db.connection())
        data['past_quantity'] = data['past_quantity'].apply(lambda x: f'{x:,.0f}')
        data['past_amount'] = data['past_amount'].apply(lambda x: f'{x :,.0f}')
        data['past_ratio'] = data['past_ratio'].apply(lambda x: f'{x :.2f}')

        data.columns = ['ETF', '종목코드', '종목명', '보유량', '보유금액', '비중']
        return {
            'data': data.reset_index(drop=True).to_json(orient='records')
        }
    except oracledb.DatabaseError as e:
        logger.error(f'[get_all_drop_data]Database operation failed: {e}')

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
    data.columns = ['국가', '날짜', '시간', '지표명', '이전 실적', '이번 예상','실제 실적','중요도']

    # 2024-11-26 중요도 데이터가 바뀌어서 수정함
    data['중요도'] = data['중요도'].apply(lambda x : x.split("_")[-1])
    data['중요도'] = data['중요도'].str.replace("high", "상")
    data['중요도'] = data['중요도'].str.replace("md", "중")
    data['중요도'] = data['중요도'].str.replace("low", "하")

    # 전처리 : 엔 표기 변경
    data[['이전 실적', '이번 예상', '실제 실적']] = data[['이전 실적', '이번 예상', '실제 실적']].apply(lambda x : x.str.replace("&yen;", "￥"))

    # 데이터 정렬
    data = data.sort_values(['날짜', '시간'])

    # 날짜 데이터 생성
    value = data['날짜'].unique().tolist()
    days = [f'{int(d[:2])}월 {int(d[-2:])}일' for d in value]
    time_diff = [f'({v}일 전)' for v in range(days_ago, 0, -1)] + ['(오늘)'] + [f'({v}일 후)' for v in range(1, days_later+1)]
    name = [v1 + v2 for v1, v2 in zip(days, time_diff)]

    date = pd.DataFrame({'value': value, 'name': name})

    return {
        'date': date.reset_index(drop=True).to_json(orient='records'),
        'data': data.reset_index(drop=True).to_json(orient='records')
    }