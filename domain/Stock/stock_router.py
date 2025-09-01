import asyncio
import numpy as np
import FinanceDataReader as fdr
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from modules.telegram import *
import html
from sqlalchemy import Float
from sqlalchemy.dialects.oracle import FLOAT as ORACLE_FLOAT

router = APIRouter(
    prefix="/Stock",
)

@router.get('/{code}/content')
async def get_stock_content(db: Session = Depends(get_db), code: str = "") :
    try :
        research, news, price, profile, change, dart = await asyncio.gather(
            get_stock_research(db, code = code),
            get_stock_news(db, code = code),
            get_stock_price(db, code = code),
            get_stock_profile(db, code = code),
            get_stock_changes(db, code=code),
            get_stock_dart(db, code=code)
        )
        return {
            "research" : research,
            "news" : news,
            "price" : price,
            "profile" : profile,
            "change" : change,
            "dart" : dart
        }

    except Exception as e:

        print(f"ERROR : {e} | CODE : {code} | DOMAIN : stock_router")

        raise HTTPException(status_code=500, detail=str(e))

async def get_stock_research(db: Session = Depends(get_db), code: str = ""):

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

        return {
            'message' : message,
            'content' : data.reset_index(drop=True).to_json(orient='split'),
        }

    except oracledb.DatabaseError as e:
        logger.error(f'[get_stock_research]Database operation failed: {e}')

async def get_stock_news(db: Session = Depends(get_db), code: str = ""):

    try :
        url = f'https://openapi.naver.com/v1/search/news.json'
        q = f"""
        SELECT "종목명"
        FROM COMPANY_INFO
        WHERE TO_CHAR("종목코드") = :code
        """
        keyword = pd.read_sql(q, con = db.connection(), params = {'code' : code})

        if len(keyword) > 0 :
            keyword = keyword['종목명'].to_list()[0]

            params = {'query': keyword,
                      'display': '50'}
            headers = {
                'X-Naver-Client-Id': config('X-Naver-Client-Id'),
                'X-Naver-Client-Secret': config('X-Naver-Client-Secret')
            }

            response = requests.get(url, params=params, headers=headers)
            newsData = pd.DataFrame(response.json()['items'])[['title', 'pubDate', 'link']]

            newsData['title'] = newsData['title'].apply(lambda x: x.replace('<b>', '').replace('</b>', ''))
            newsData['title'] = newsData['title'].apply(lambda x : html.unescape(x))
            newsData['pubDate'] = pd.to_datetime(newsData['pubDate'])
            newsData['pubDate'] = newsData['pubDate'].apply(lambda x: x.strftime('%Y-%m-%d'))

            newsData.columns = ['기사 제목', '날짜', '링크']
            newsData.sort_values('날짜', ascending=False)

            return newsData.reset_index(drop=True).to_json(orient='split')
        else :
            return {
                '기사제목' : None,
                '날짜' : None,
                '링크' : None,
            }

    except oracledb.DatabaseError as e:
        logger.error(f'[get_stock_news]Database operation failed: {e}')

async def get_stock_price(db: Session = Depends(get_db), code: str = ""):


    try :
        tz = pytz.timezone('Asia/Seoul')
        now = datetime.now(tz)
        today = now.strftime('%Y-%m-%d')
        month_ago = now - timedelta(days=90)
        month_ago = month_ago.strftime('%Y-%m-%d')

        price = fdr.DataReader(f"{code}", start=month_ago, end=today).reset_index()
        price = price[['Date', 'Close']]
        price['Date'] = price['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))


        q = """
        SELECT *
        FROM stock_target
        WHERE code = :code
        """
        target = pd.read_sql(q, con=db.connection(), params = {'code' : code})

        if target.shape[0] != 0:
            target = target.loc[target['code'] == code, ['Date', 'target']]
            price = price.merge(target, on='Date')

        else:
            price['target'] = None

        return {
            'date' : price.reset_index()['Date'].to_list(),
            'close': round(price['Close'], 0).to_list(),
            'target': round(price['target'], 0).to_list(),
            }

    except oracledb.DatabaseError as e:
        logger.error(f'[get_code_price]Database operation failed: {e}')

async def get_stock_profile(db: Session = Depends(get_db), code: str = "") :

    try :
        q1 = """
        SELECT 종목명, 대표자명, 홈페이지, 설립일
        FROM company_info 
        WHERE TO_CHAR("종목코드") = :code
        """
        company_info = pd.read_sql(q1, con = db.connection(), params={'code':code})
        company_info['설립일'] = pd.to_datetime(company_info['설립일'])
        company_info['설립일'] = company_info['설립일'].apply(lambda x : f"{x.year}년 {x.month}월 {x.day}일")



        q3 = """
        SELECT 상장일, 시장구분, 주식종류, 액면가, 상장주식수
        FROM stock_profile
        WHERE TO_CHAR("단축코드") = :code
        """
        krx = pd.read_sql(q3, con = db.connection(), params={'code' : code})
        krx['상장일'] = pd.to_datetime(krx['상장일'])
        krx['상장일'] = krx['상장일'].apply(lambda x : f"{x.year}년 {x.month}월 {x.day}일")

        result = pd.concat([company_info, krx], axis = 1)
        result['홈페이지'] = "https://" + result['홈페이지']


        q4 = """
        SELECT "레이블"
        FROM research_label
        WHERE TO_CHAR("종목코드") = :code
        """
        label = pd.read_sql(q4, con=db.connection(), params={'code' : code})['레이블'].to_list()
        if len(label) > 0 :
            result['레이블'] = ",".join(label)
            result['레이블수'] = len(label)
        else :
            result['레이블'] = None

        q5 = """
        SELECT "업종명"
        FROM wics
        WHERE TO_CHAR("종목코드") = :code
        """

        industry = pd.read_sql(q5, con=db.connection(), params={'code' : code})['업종명'].to_list()
        if len(industry) > 0 :
            result['업종'] = ",".join(industry)
        else :
            result['업종'] = None

        q6 = """
        SELECT "테마명"
        FROM theme_label
        WHERE TO_CHAR("종목코드") = :code
        ORDER BY TO_NUMBER("테마점수") DESC
        """
        theme = pd.read_sql(q6, con=db.connection(), params={'code' : code}).drop_duplicates()
        result['테마수'] = len(theme)
        if len(theme) > 0 :
            result['테마'] = ", ".join(theme.head()['테마명'].to_list())
        else :
            result['테마'] = None

        if len(result) > 0 :
            return result.to_dict(orient='records')[0]

        else :
            return None

    except oracledb.DatabaseError as e:
        logger.error(f'[get_stock_profile]Database operation failed: {e}')

        return None


async def get_stock_changes(db: Session = Depends(get_db), code: str = "") :

    try :
        q1 = f"""
            SELECT *
            FROM etf_base_table
            WHERE stock_code = :code
            """
        data = pd.read_sql(q1, con = db.connection(), params={'code':code})
        data['diff_p'] = (data['recent_amount'] / data['recent_quantity']) - (data['past_amount'] / data['past_quantity'])       
        data['status_r'] = [
            '상승📈' if r > 0 else
            '하락📉' if r < 0 else
            '변화없음💬' for r in round(data['diff_ratio'], 2)
        ]

        data['status_p'] = [
            '상승📈' if p > 0 else
            '하락📉' if p < 0 else
            '변화없음💬' for p in data['diff_p']   
        ]

        data['status_q'] = [
            '상승📈' if q > 0 else
            '하락📉' if q < 0 else
            '변화없음💬' for q in data['diff_quantity']    
        ]

        con = (data['recent_ratio'] > 0) & (data['past_ratio'] == 0)
        data.loc[con, ['status_r', 'status_p', 'status_q']] = ['신규🆕', '-', '-']

        con = (data['recent_ratio'] == 0) & (data['past_ratio'] > 0)
        data.loc[con, ['status_r', 'status_p', 'status_q']] = ['Drop🔚', '-', '-']
        
        data = data[['etf_name', 'status_r', 'status_p', 'status_q', 'recent_ratio', 'past_ratio', 'diff_ratio', 'diff_amount']]
        data['recent_ratio'] = round(data['recent_ratio'], 2)
        data['past_ratio'] = round(data['past_ratio'], 2)
        data['diff_ratio'] = round(data['diff_ratio'], 2)

        data.columns = ['ETF명', '비중', '가격', '수량', '최근 비중(%)', '일주일 전 비중(%)', '비중 차이(%p)', '증감액(원)']
        data = data.sort_values('증감액(원)', ascending=False)
        data = data.dropna()
        
        return data.reset_index(drop=True).to_json(orient='split')
    except oracledb.DatabaseError as e:
        logger.error(f'[get_stock_of_etf_data]Database operation failed: {e}')

async def get_stock_dart(db: Session = Depends(get_db), code: str = "") :

    try :
    
        q1 = """
        SELECT * 
        FROM code_table 
        WHERE TO_CHAR(code) = :code
        """

        code_table = pd.read_sql(q1, con = db.connection(), params={'code':code})
        dart_code = code_table['dart_code'].values[0]

        tz = pytz.timezone('Asia/Seoul')
        now = datetime.now(tz)
        date = (now - timedelta(days=90)).strftime('%Y%m%d')

        url = 'https://opendart.fss.or.kr/api/list.json'
        params = {
            'crtfc_key' : config('DART_API_KEY'),
            'corp_code' : dart_code,
            'bgn_de' : date,
        }

        response = requests.get(url, params=params)
        data = response.json()
        data = pd.DataFrame(data['list'])

        data['url'] = 'https://dart.fss.or.kr/dsaf001/main.do?rcpNo=' + data['rcept_no']
        data['rcept_dt'] = pd.to_datetime(data['rcept_dt'])
        data['rcept_dt'] = data['rcept_dt'].dt.strftime('%Y-%m-%d')

        data = data[['report_nm', 'flr_nm', 'rcept_dt', 'url']]
        data.columns = ['보고서명', '제출인명','제출일자' , '링크']

        return data.to_json(orient='split')
    except oracledb.DatabaseError as e:
        logger.error(f'[get_stock_dart]Database operation failed: {e}')
