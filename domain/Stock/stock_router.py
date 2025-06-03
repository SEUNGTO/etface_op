from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from config import *
import pandas as pd
import numpy as np
import requests
import FinanceDataReader as fdr
from datetime import datetime, timedelta
import pytz
from modules.telegram import *

router = APIRouter(
    prefix="/Stock",
)


@router.get('/research/{code}')
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

@router.get('/news/{code}')
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

@router.get('/telegram/{code}')
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

# Stock function
@router.get('/{code}/price')
def get_code_price(db: Session = Depends(get_db), code: str = ""):
    try :
        tz = pytz.timezone('Asia/Seoul')
        now = datetime.now(tz)
        today = now.strftime('%Y-%m-%d')
        month_ago = now - timedelta(days=90)  # 사실은 3달 전
        month_ago = month_ago.strftime('%Y-%m-%d')

        price = fdr.DataReader(f"{code}", start=month_ago, end=today).reset_index()
        price = price[['Date', 'Close']]
        price['Date'] = price['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))

        target = pd.DataFrame({})
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

@router.get('/{code}/price/describe')
def get_code_price_describe(db: Session = Depends(get_db), code: str = "", _type: str = ""):
    try :
        tz = pytz.timezone('Asia/Seoul')
        now = datetime.now(tz)
        today = now.strftime('%Y-%m-%d')
        month_ago = now - timedelta(days=90)  # 사실은 3달 전
        month_ago = month_ago.strftime('%Y-%m-%d')

        price = fdr.DataReader(f"{code}", start=month_ago, end=today).reset_index()
        price = price[['Date', 'Close']]
        price['Date'] = price['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))

        current = price['Close'][price['Date'].idxmax()]

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



@router.get("/{code}/{order}")
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
