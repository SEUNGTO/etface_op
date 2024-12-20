from fastapi import FastAPI, Depends
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from config import *
import requests
import pandas as pd
import FinanceDataReader as fdr
from bs4 import BeautifulSoup
import pytz
from datetime import datetime, timedelta
import numpy as np

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


# ETF SECTION 1-1 : top10 chart
@app.get("/ETF/{code}/top10")
def get_etf_data(db: Session = Depends(get_db), code: str = ""):
    try :
        q1 = f"""
        SELECT stock_name, recent_ratio
        FROM etf_base_table
        WHERE etf_code = '{code}'
        and recent_ratio <> 0
        """

        data = pd.read_sql(q1, con = db.connection())
        data = data.sort_values('recent_ratio', ascending=False)
        data = data.head(10).reset_index(drop=True)
        data.loc['기타', :] = ["기타", 100 - data['recent_ratio'].sum()]
        data['recent_ratio'] = data['recent_ratio'].apply(lambda x: f'{x :.2f}')
        data.columns = ['종목명', '비중']

        result = {}
        for idx, item in data.iterrows():
            result[item['종목명']] = item['비중']

        return result

    except oracledb.DatabaseError as e:
        logger.error(f'[get_etf_data] Database operation failed: {e}')


# ETF SECTION 1-2 : detail deposit
@app.get('/ETF/{code}/depositDetail')
def get_detail_data(db: Session = Depends(get_db), code:str = ""):
    try :
        q1 = f"""
        SELECT 
            stock_code
            , stock_name
            , recent_ratio
        FROM etf_base_table
        WHERE etf_code = '{code}'
            and recent_ratio <> 0
        """
        data = pd.read_sql(q1, con = db.connection())

        q2 = """
        SELECT  stock_code
                ,stock_target_price
                ,report_title
                ,report_opinion
                ,report_pubdate
                ,report_researcher
                ,report_link
        FROM etf_deposit_detail
        """
        research = pd.read_sql(q2, con = db.connection())

        data = data.merge(research, how='left', on='stock_code')
        data = data.sort_values('recent_ratio', ascending=False)
        data.drop('stock_code', axis=1, inplace=True)

        data['recent_ratio'] = data['recent_ratio'].apply(lambda x: f'{x :.2f}')
        data['stock_target_price'] = data['stock_target_price'].apply(lambda x: None if x == "" else f'{x :,.0f}')

        data.columns = ['종목명', '비중', '목표가', '리포트 제목', '의견', '게시일자', '증권사', '링크']

        result = {'status': 'successful'}

        return {
            'message': result,
            'data': data.reset_index(drop=True).to_json(orient='records')
        }
    except oracledb.DatabaseError as e:
        logger.error(f'[get_detail_data]Database operation failed: {e}')


# ETF SECTION 2 : telegram
@app.get('/ETF/telegram/{code}')
def get_etf_telegram_data(db: Session = Depends(get_db), code: str = ""):
    try :
        q1 = f"""
        SELECT *
        FROM (
            SELECT
                stock_name
            FROM etf_base_table
            WHERE etf_code = '{code}'
                and recent_ratio <> 0
            ORDER BY recent_ratio DESC
            )
        WHERE ROWNUM <= 5
        """
        stocks = pd.read_sql(q1, con = db.connection())['stock_name'].tolist()
        data = clean_telegram_data(stocks)
        return {'list': stocks,
                'data': data.reset_index(drop=True).to_json(orient='records')}
    except oracledb.DatabaseError as e:
        logger.error(f'[get_etf_telegram_data] Database operation failed: {e}')

# ETF SECTION 3 : price
@app.get('/{_type}/{code}/price')
def get_code_price(db: Session = Depends(get_db), code: str = "", _type: str = ""):
    try :
        tz = pytz.timezone('Asia/Seoul')
        now = datetime.now(tz)
        today = now.strftime('%Y-%m-%d')
        month_ago = now - timedelta(days=90)  # 사실은 3달 전
        month_ago = month_ago.strftime('%Y-%m-%d')

        price = fdr.DataReader(code, start=month_ago, end=today).reset_index()
        price = price[['Date', 'Close']]
        price['Date'] = price['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))

        target = pd.DataFrame({})
        if _type == "ETF":
            q = f"""
            SELECT *
            FROM etf_target
            WHERE code = '{code}'
            """
            target = pd.read_sql(q, con = db.connection())
            target['target'] = standardize_price(target['target'])
        elif _type == "Stock":
            q = f"""
            SELECT *
            FROM stock_target
            WHERE code = '{code}'
            """
            target = pd.read_sql(q, con=db.connection())

        if target.shape[0] != 0:
            target = target.loc[target['code'] == code, ['Date', 'target']]
            price = price.merge(target, on='Date')

        else:
            price['target'] = None

        return price.to_dict()

    except oracledb.DatabaseError as e:
        logger.error(f'[get_code_price]Database operation failed: {e}')

@app.get('/{_type}/{code}/price/describe')
def get_code_price_describe(db: Session = Depends(get_db), code: str = "", _type: str = ""):
    try :
        tz = pytz.timezone('Asia/Seoul')
        now = datetime.now(tz)
        today = now.strftime('%Y-%m-%d')
        month_ago = now - timedelta(days=90)  # 사실은 3달 전
        month_ago = month_ago.strftime('%Y-%m-%d')

        price = fdr.DataReader(code, start=month_ago, end=today).reset_index()
        price = price[['Date', 'Close']]
        price['Date'] = price['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))

        current = price['Close'][price['Date'].idxmax()]

        if _type == 'Stock' :

            q = f"""
            SELECT AVG(target) as avg
            FROM stock_target
            WHERE code = '{code}' 
            """
            avg_target = pd.read_sql(q, con = db.connection()).values.max()

            if avg_target is not None :
                target_ratio = current / avg_target * 100
                to_target = (100/target_ratio - 1) * 100
            else :
                target_ratio = 0
                to_target = 0

        else :
            # ETF일 때도 설정해야 함
            target_ratio = 0
            to_target = 0

        highest = price['Close'].max()
        highest_ratio = (highest / current - 1) * 100

        lowest = price['Close'].min()
        lowest_ratio = (lowest / current - 1) * -100

        return {
            'target_ratio' : f"{target_ratio:.2f}",
            'to_target' : f"{to_target:.2f}",
            'highest' : f"{highest:,.0f}",
            'highest_ratio' : f"{highest_ratio:.2f}",
            'lowest' : f"{lowest:,.0f}",
            'lowest_ratio' : f"{lowest_ratio:.2f}",
        }
    except oracledb.DatabaseError as e:
        logger.error(f'[get_code_price_describe]Database operation failed: {e}')


@app.get("/ETF/{code}/{order}")
def get_etf_data_by_order(db: Session = Depends(get_db), code: str = "", order: str = ""):

    try :
        q1 = f"""
        SELECT stock_name, recent_ratio, past_ratio, diff_ratio
        FROM etf_base_table
        WHERE etf_code = '{code}'
        """
        data = pd.read_sql(q1, con = db.connection())

        if order == 'increase':
            ind = (data['recent_ratio'] != 0) & (data['diff_ratio'] > 0)
            data = data.loc[ind, :]
            data = data.sort_values('diff_ratio', ascending=False)
        elif order == 'decrease':
            ind = (data['recent_ratio'] != 0) & (data['diff_ratio'] < 0)
            data = data.loc[ind, :]
            data = data.sort_values('diff_ratio', ascending=True)
        elif order == 'new':
            ind = (data['past_ratio'] == 0) & (data['recent_ratio'] != 0)
            data = data.loc[ind, :]
            data = data.sort_values('diff_ratio', ascending=False)
        elif order == 'drop':
            ind = (data['past_ratio'] != 0) & (data['recent_ratio'] == 0)
            data = data.loc[ind, :]
            data = data.sort_values('diff_ratio', ascending=True)

        data = data.head(10)
        data['recent_ratio'] = data['recent_ratio'].apply(lambda x: f'{x :.2f}')
        data['past_ratio'] = data['past_ratio'].apply(lambda x: f'{x :.2f}')
        data['diff_ratio'] = data['diff_ratio'].apply(lambda x: f'{x :.2f}')
        data.columns = ['종목명', '비중(기준일)', '비중(비교일)', '차이']

        return data.reset_index(drop=True).to_json(orient='records')

    except oracledb.DatabaseError as e:
        logger.error(f'[get_etf_data_by_order] Database operation failed: {e}')

## Stock function
@app.get('/Stock/research/{code}')
def get_stock_research(db: Session = Depends(get_db), code: str = ""):
    # 나중에 쿼리 튜닝 필요
    try :
        data = pd.read_sql('SELECT * FROM research', con = db.connection())
        data = data.drop_duplicates()
        cols = ['리포트 제목', '목표가', '의견', '게시일자', '증권사', '링크']
        data = data.loc[data['종목코드'] == code, cols]

        if len(data) > 0 :

            maxIdx = data['목표가'].astype(float).idxmax()
            if maxIdx is np.nan :
                maxResearcher = None
                maxPrice = None
            else :
                maxResearcher = data.loc[maxIdx, '증권사']
                maxPrice = data.loc[maxIdx, '목표가']
                maxPrice = f'{float(maxPrice):,.0f}'

            minIdx = data['목표가'].astype(float).idxmin()
            if minIdx is np.nan :
                minResearcher = None
                minPrice = None
            else :
                minResearcher = data.loc[minIdx, '증권사']
                minPrice = data.loc[minIdx, '목표가']
                minPrice = f'{float(minPrice):,.0f}'

            avgPrice = data['목표가'].astype(float).mean()
            if avgPrice is np.nan :
                avgPrice = None
            else :
                avgPrice = f'{float(avgPrice):,.0f}'
            message = {
                'length' : len(data),
                'avgPrice' : avgPrice,
                'maxPrice' : maxPrice,
                'maxResearcher' : maxResearcher,
                'minPrice' : minPrice,
                'minResearcher': minResearcher
            }

            data['목표가'] = data['목표가'].apply(lambda x: None if x == "" or x == None else f'{float(x) :,.0f}')
            data = data.sort_values('게시일자', ascending=False)
            data.fillna("", inplace = True)
        else :
            message = {
                'length': "0",
                'avgPrice': None,
                'maxPrice': None,
                'maxResearcher': None,
                'minPrice': None,
                'minResearcher': None
            }

        return {'message': message,
                'data': data.reset_index(drop=True).to_json(orient='records')}

    except oracledb.DatabaseError as e:
        logger.error(f'[get_stock_research]Database operation failed: {e}')

## Stock function
@app.get('/Stock/news/{code}')
def get_stock_news(db: Session = Depends(get_db), code: str = ""):

    try :
        url = f'https://openapi.naver.com/v1/search/news.json'
        q = f"""
        SELECT *
        FROM (SELECT stock_name
                FROM etf_base_table
                WHERE stock_code = '{code}')
        WHERE ROWNUM <= 1
        """
        keyword = pd.read_sql(q, con = db.connection())

        if len(keyword) > 0 :
            keyword = keyword['stock_name'].to_list()[0]

            params = {'query': keyword,
                      'display': '50'}
            headers = {
                'X-Naver-Client-Id': config('X-Naver-Client-Id'),
                'X-Naver-Client-Secret': config('X-Naver-Client-Secret')
            }

            response = requests.get(url, params=params, headers=headers)
            newsData = pd.DataFrame(response.json()['items'])[['title', 'pubDate', 'link']]

            newsData['title'] = newsData['title'].apply(lambda x: x.replace('<b>', '').replace('</b>', ''))
            newsData['pubDate'] = pd.to_datetime(newsData['pubDate'])
            newsData['pubDate'] = newsData['pubDate'].apply(lambda x: x.strftime('%Y-%m-%d'))

            newsData.columns = ['기사 제목', '날짜', '링크']
            newsData.sort_values('날짜', ascending=False)

            status = {'message': 'successful'}
            return {'message': status,
                    'data': newsData.reset_index(drop=True).to_json(orient='records')}

    except oracledb.DatabaseError as e:
        logger.error(f'[get_stock_news]Database operation failed: {e}')

@app.get('/Stock/telegram/{code}')
def get_stock_telegram_data(db: Session = Depends(get_db), code: str = ""):

    try :
        q1 = f"""
        SELECT *
        FROM (
            SELECT
                stock_name
            FROM etf_base_table
            WHERE stock_code = '{code}'
                and recent_ratio <> 0
            ORDER BY recent_ratio DESC
            )
        WHERE ROWNUM <= 1
        """
        stocks = pd.read_sql(q1, con = db.connection())['stock_name'].tolist()
        data = clean_telegram_data(stocks)

        return data.reset_index(drop=True).to_json(orient='records')

    except oracledb.DatabaseError as e:
        logger.error(f'[get_stock_telegram_data]Database operation failed: {e}')


@app.get("/Stock/{code}/{order}")
def get_stock_of_etf_data(db: Session = Depends(get_db), code: str = "", order: str = ""):

    try :
        q1 = f"""
        SELECT etf_name, recent_ratio, past_ratio, diff_ratio
        FROM etf_base_table
        WHERE stock_code = '{code}'
        """
        data = pd.read_sql(q1, con = db.connection())

        if order == 'largeRatio':
            ind = (data['recent_ratio'] != 0)
            data = data.loc[ind, :]
            data = data.sort_values('recent_ratio', ascending=False)

        elif order == 'increase':
            ind = (data['recent_ratio'] != 0) & (data['diff_ratio'] > 0)
            data = data.loc[ind, :]
            data = data.sort_values('diff_ratio', ascending=False)
        elif order == 'decrease':
            ind = (data['recent_ratio'] != 0) & (data['diff_ratio'] < 0)
            data = data.loc[ind, :]
            data = data.sort_values('diff_ratio', ascending=True)
        elif order == 'new':
            ind = (data['past_ratio'] == 0) & (data['recent_ratio'] != 0)
            data = data.loc[ind, :]
            data = data.sort_values('diff_ratio', ascending=False)
        elif order == 'drop':
            ind = (data['past_ratio'] != 0) & (data['recent_ratio'] == 0)
            data = data.loc[ind, :]
            data = data.sort_values('diff_ratio', ascending=True)

        data = data.head(10)
        data['recent_ratio'] = data['recent_ratio'].apply(lambda x: f'{x :.2f}')
        data['past_ratio'] = data['past_ratio'].apply(lambda x: f'{x :.2f}')
        data['diff_ratio'] = data['diff_ratio'].apply(lambda x: f'{x :.2f}')
        data.columns = ['ETF', '비중(기준일)', '비중(비교일)', '차이']

        return data.reset_index(drop=True).to_json(orient='records')

    except oracledb.DatabaseError as e:
        logger.error(f'[get_stock_of_etf_data]Database operation failed: {e}')

def telegram_crawller(url, keyword):
    telegram_msgs = {
        'msg': []
        , 'date': []
        , 'time': []
        , 'view': []
        , 'link': []
    }
    query = f'{url}?q={keyword}'
    response = requests.get(query)
    soup = BeautifulSoup(response.content, 'html.parser')

    for msg in soup.find_all('div', class_='tgme_widget_message_bubble'):

        msg.find('a').decompose()
        _view = msg.find('span', class_='tgme_widget_message_views').text

        try:
            _msg = msg.find('div', class_='tgme_widget_message_text js-message_text').text

            datetime = pd.to_datetime(msg.find('time', class_='time').attrs['datetime'])
            datetime = datetime.tz_convert('Asia/Seoul')
            _date = datetime.strftime('%Y-%m-%d')
            _time = datetime.strftime('%H:%M')

            telegram_msgs['msg'].append(_msg)
            telegram_msgs['date'].append(_date)
            telegram_msgs['time'].append(_time)
            telegram_msgs['view'].append(_view)

        except:
            _msg = None
            telegram_msgs['msg'].append(_msg)
            telegram_msgs['date'].append("-")
            telegram_msgs['time'].append("-")
            telegram_msgs['view'].append(_view)

    for uu in soup.find_all('a', class_='tgme_widget_message_date'):
        _link = uu.attrs['href']
        telegram_msgs['link'].append(_link)

    telegram_msgs = pd.DataFrame(telegram_msgs)
    telegram_msgs.columns = ['메세지', '일자', '시간', '조회수', '링크']
    telegram_msgs.sort_values(by=['일자', '시간'], ascending=[False, False], inplace=True)

    return telegram_msgs.dropna()


def clean_telegram_data(stocks):
    data = pd.DataFrame({})
    for channel, url in telegram_dict.items():
        for stock in stocks:
            try:
                msg = telegram_crawller(url, stock)
                msg['시간'] = msg['일자'] + " " + msg['시간']
                msg.drop('일자', axis=1, inplace=True)
                msg['종목명'] = stock
                msg['채널명'] = channel
                msg = msg[['채널명', '종목명', '조회수', '링크', '시간', '메세지']]
                msg.reset_index(drop=True)
                data = pd.concat([data, msg])
            except:
                continue
    data = data.sort_values('시간', ascending=False)
    return data


def standardize_price(data):
    _med = data.median()
    centered = data - _med

    _max = centered.max()
    _min = centered.min()

    _stdData = 2 * (centered - _min) / (_max - _min) - 1
    return _stdData * 100
