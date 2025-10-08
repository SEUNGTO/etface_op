import json
import asyncio
import FinanceDataReader as fdr
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from modules.telegram import *

router = APIRouter(
    prefix="/ETF",
)

@router.get('/{code}/content')
async def get_etf_content(db: Session = Depends(get_db), code: str = "") :
    try :
        profile, price, top10, similar, finance, deposit, change, byIndustry = await asyncio.gather(
            get_etf_profile(db, code = code),
            get_etf_price(db, code = code),
            get_etf_top10(db, code = code),
            get_etf_similar(db, code = code),
            get_etf_finance(db, code=code),
            get_etf_deposit(db, code=code),
            get_etf_change(db, code=code),
            get_etf_by_industry(db, code = code)
        )

        return {
            "profile" : profile,
            "price" : price,
            "top10" : top10,
            "similar" : similar,
            "finance" : finance,
            "deposit" : deposit,
            "change" : change,
            "byIndustry" : byIndustry,
        }

    except Exception as e:
        import pytz
        from datetime import datetime
        tz = pytz.timezone('Asia/Seoul')
        error = pd.DataFrame({'error' : e, 'code' : code, 'date' : datetime.now(tz).timestamp(),'domain' : 'etf_router'})
        error.to_sql('error', con = db.connection(), if_exists='append', index=False)
        raise HTTPException(status_code=500, detail=str(e))

async def get_etf_profile(db: Session = Depends(get_db), code: str = ""):

    try : 
        tz = pytz.timezone('Asia/Seoul')
        now = datetime.now(tz)
        today = datetime(now.year, now.month, now.day)

        query = """
        SELECT "상장일", "기초지수명", "지수산출기관",
            "복제방법", "기초시장분류", "기초자산분류",
            "운용사", "CU수량", "총보수", "과세유형"
        FROM etf_info
        WHERE "단축코드" = :code
        """
        data = pd.read_sql(query, con = db.connection(), params = {'code' : code})

        list_date = pd.to_datetime(data['상장일'].values[0])
        days = (today - list_date).days
        asset = data['기초자산분류'].values[0]
        market = data['기초시장분류'].values[0]
        pay = f"{data['총보수'].values[0]}%"
        tax = data['과세유형'].values[0]
        
        track_index = data['기초지수명'].values[0]
        tracker = data['지수산출기관'].values[0]
        
        operator = data['운용사'].values[0]
        method = data['복제방법'].values[0].split("(")[-1].replace(")", "")

        q = """
            SELECT "ETF점수", "ETF레이블"
            FROM etf_label
            WHERE TO_CHAR("ETF코드") = :code
            """
        labels = pd.read_sql(q, con = db.connection(), params={'code' : code})
        label = labels['ETF레이블'].values[0]
        score = round(labels['ETF점수'].values[0]*100, 2)
        
        profile = {
            "운용사" : operator,
            '시장' : market,
            '기초자산' : asset,
            "스타일" : method,
            "산출기관" : tracker,
            "기초지수" : track_index,
            "상장일" : f"{list_date.year}년 {list_date.month}월 {list_date.day}일",

            "상장일수" : days,
            '과세' : tax,
            '총보수' : pay,
            '레이블' : label,
            '점수' : score,
            }

        return profile

    except oracledb.DatabaseError as e:
        logger.error(f'[get_etf_data_by_order] Database operation failed: {e}')

async def get_etf_price(db: Session = Depends(get_db), code: str = ""):
    try :
        tz = pytz.timezone('Asia/Seoul')
        now = datetime.now(tz)
        today = now.strftime('%Y-%m-%d')
        month_ago = now - timedelta(days=90)  # 사실은 3달 전
        month_ago = month_ago.strftime('%Y-%m-%d')

        price = fdr.DataReader(f"NAVER:{code}", start=month_ago, end=today).reset_index()
        price = price[['Date', 'Close']]
        price['Date'] = price['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))

        target = pd.DataFrame({})
        q = """
        SELECT *
        FROM etf_target
        WHERE code = :code
        """
        target = pd.read_sql(q, con = db.connection(), params = {'code' : code})
        target['target'] = standardize_price(target['target'])

        if target.shape[0] != 0:
            target = target.loc[target['code'] == code, ['Date', 'target']]
            price = price.merge(target, on='Date')

        else:
            price['target'] = None

        return {
            'date' : price.reset_index()['Date'].to_list(),
            'close' : price['Close'].to_list(),
            'target' : price['target'].to_list(),
        }

    except oracledb.DatabaseError as e:
        logger.error(f'[get_code_price]Database operation failed: {e}')

async def get_etf_top10(db: Session = Depends(get_db), code: str = ""):
    try :
        q1 = """
        SELECT stock_name, recent_ratio
        FROM etf_base_table
        WHERE etf_code = :code
        and recent_ratio <> 0
        """

        data = pd.read_sql(q1, con = db.connection(), params = {'code' : code})
        data = data.sort_values('recent_ratio', ascending=False)
        data = data.head(10).reset_index(drop=True)
        data.loc['기타', :] = ["기타", 100 - data['recent_ratio'].sum()]
        data['recent_ratio'] = data['recent_ratio'].apply(lambda x: round(x, 2))
        data.columns = ['종목명', '비중']

        return {
            'label' : data['종목명'].to_list(),
            'ratio' : data['비중'].to_list()
        }

    except oracledb.DatabaseError as e:
        logger.error(f'[get_etf_data] Database operation failed: {e}')

async def get_etf_similar(db: Session = Depends(get_db), code: str = ""):
    try :
        safe_query = "SELECT distinct etf_code FROM etf_base_table WHERE etf_code = :code"
        whiteCode = pd.read_sql(safe_query, con = db.connection(), params={'code' : code})
        whiteCode = whiteCode['etf_code'].to_list()[0]
        q1 = f"""
            SELECT etf_name, etf_code, stock_name, recent_ratio
            FROM etf_base_table
            WHERE 1 = 1
            and etf_code in (
                SELECT CAST ("{whiteCode}" AS VARCHAR(50))
                FROM similar_etf
                )
            and recent_ratio <> 0
            """
        data = pd.read_sql(q1, con = db.connection())
        subset_name = data['etf_name'].drop_duplicates().to_list()
        response = []

        for sub_name in subset_name :

            buffer = {}
            tmp = data.loc[data['etf_name'] == sub_name, ['stock_name', 'recent_ratio']]
            tmp = tmp.sort_values('recent_ratio', ascending=False)
            tmp = tmp.head(10).reset_index(drop=True)
            tmp.loc['기타', :] = ["기타", 100 - tmp['recent_ratio'].sum()]
            tmp['recent_ratio'] = tmp['recent_ratio'].apply(lambda x: f'{x :.2f}')
            tmp.columns = ['종목명', '비중']
            for _, item in tmp.iterrows() :
                buffer[item['종목명']] = item['비중']
            
            response.append(buffer)

        name = data[['etf_name']].drop_duplicates()
        name = name.rename(columns = {'etf_name' : 'name'})
        name['value'] = [0,1,2,3,4]

        return {
            'name' : name.to_json(orient='records'),
            'data' : json.dumps(response),
        }

    except oracledb.DatabaseError as e:
        logger.error(f'[get_etf_data] Database operation failed: {e}')

async def get_etf_finance(db: Session = Depends(get_db), code: str = ""):

    try:
        query = f"""
            SELECT *
            FROM fs_etf_table
            WHERE TO_CHAR(etf_code) = :code
            ORDER BY date_order
        """

        data = pd.read_sql(query, con=db.connection(), params={'code': code})
        data= data.pivot_table(index = 'account_name', columns = 'bas_date', values = 'amount')
        index = [
            '유동자산', '현금및현금성자산', '재고자산', '매출채권', '비유동자산', '자산총계',
            '유동부채', '매입채무', '비유동부채', '부채총계',
            '자본금', '이익잉여금', '자본총계',
            '매출액', '영업이익', '법인세차감전 순이익', '당기순이익(손실)',
        ]
        data = data.loc[index]

        q = """SELECT "CU수량" FROM etf_info WHERE TO_CHAR("단축코드") = :code"""
        n_cu = pd.read_sql(q, con=engine, params={'code': code})
        n_cu = n_cu['CU수량'].values[0]
        price = fdr.DataReader(f"NAVER:{code}")['Close'].tail(1).values[0]

        ratio = pd.DataFrame()
        ratio['순이익률(%)'] = round(data.loc['당기순이익(손실)'] / data.loc['매출액'] * 100, 2)
        ratio['ROE(자기자본이익률, %)'] = round(data.loc['당기순이익(손실)'] / data.loc['자본총계'] * 100, 2)
        ratio['ROA(총자산이익률, %)'] = round(data.loc['당기순이익(손실)'] / data.loc['자산총계'] * 100, 2)
        ratio['부채비율(%)'] = round(data.loc['부채총계'] / data.loc['자본총계'] * 100, 2)
        ratio['유동비율(%)'] = round(data.loc['유동자산'] / data.loc['유동부채'] * 100, 2)

        ratio['EPS'] = round(data.loc['당기순이익(손실)'] / int(n_cu), 0)
        ratio['BPS'] = round(data.loc['자본총계'] / int(n_cu), 0)
        ratio['PER'] = round(price / (data.loc['당기순이익(손실)'] / int(n_cu)), 2)
        ratio['PBR'] = round(price / (data.loc['자본총계'] / int(n_cu)), 2)

        ratio['매출채권회전율'] = round(data.loc['매출액'] / data.loc['매출채권'], 2)
        ratio['재고자산회전율'] = round(data.loc['매출액'] / data.loc['재고자산'], 2)
        ratio['매입채무회전율'] = round(data.loc['매출액'] / data.loc['매입채무'], 2)

        ratio['매출채권회전일수'] = round(365 / (data.loc['매출액'] / data.loc['매출채권']), 2)
        ratio['재고자산회전일수'] = round(365 / (data.loc['매출액'] / data.loc['재고자산']), 2)
        ratio['매입채무회전일수'] = round(365 / (data.loc['매출액'] / data.loc['매입채무']), 2)
        ratio['현금순환주기(CCC)'] = ratio['매출채권회전일수'] + ratio['재고자산회전일수'] - ratio['매입채무회전일수']

        data.index.name = '계정명'
        data = data.reset_index()

        ratio = ratio.T
        ratio.index.name = '지표명'
        ratio = ratio.reset_index()

        return {
            'account': data.to_json(orient='records'),
            'ratio': ratio.to_json(orient='records'),
        }

    except oracledb.DatabaseError as e:
        logger.error(f'[get_etf_finance] Database operation failed: {e}')
        return {
            'account': None,
            'ratio': None,
        }

async def get_etf_deposit(db: Session = Depends(get_db), code:str = ""):
    try :
        q1 = f"""
        SELECT 
            stock_code
            , stock_name
            , recent_ratio
        FROM etf_base_table
        WHERE etf_code = :code
            and recent_ratio <> 0
        """
        data = pd.read_sql(q1, con = db.connection(), params = {'code' : code})

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
        data.columns = ['종목명', '비중', '평균 목표가', '최근 리포트', '의견', '게시일자', '증권사', '링크']

        return data.reset_index(drop=True).to_json(orient='split')

    except oracledb.DatabaseError as e:
        logger.error(f'[get_detail_data]Database operation failed: {e}')

async def get_etf_change(db: Session = Depends(get_db), code: str = ""):

    try :
        q1 = f"""
        SELECT *
        FROM etf_base_table
        WHERE etf_code = :code
        """
        data = pd.read_sql(q1, con = db.connection(), params = {'code' : code})
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

        data = data[['stock_name', 'status_r', 'status_p', 'status_q','recent_ratio', 'past_ratio', 'diff_ratio', 'diff_amount' ]]
        data['recent_ratio'] = round(data['recent_ratio'], 2)
        data['past_ratio'] = round(data['past_ratio'], 2)
        data['diff_ratio'] = round(data['diff_ratio'], 2)

        data.columns = ['종목명', '비중', '가격', '수량', '최근 비중(%)', '일주일 전 비중(%)', '비중 차이(%p)', '증감액']
        data = data.sort_values('증감액', ascending=False)
        data.dropna(inplace = True)
        return data.reset_index(drop=True).to_json(orient='split')

    except oracledb.DatabaseError as e:
        logger.error(f'[get_etf_change] Database operation failed: {e}')

async def get_etf_by_industry(db: Session = Depends(get_db), code: str = ""):
    q = f"""
        SELECT ROUND(T1.recent_ratio, 2) AS "비중",
               T2."업종명"
        FROM (
            SELECT 
                stock_code,
                recent_ratio
            FROM etf_base_table
            WHERE etf_code = :code
              AND recent_ratio <> 0
        ) T1
        LEFT JOIN (
            SELECT "업종명", "종목코드"
            FROM wics
        ) T2
          ON TO_CHAR(T1.stock_code) = TO_CHAR(T2."종목코드")
    """

    data = pd.read_sql(q, con=db.connection(), params={'code': code})
    grpSum = data.groupby('업종명')['비중'].sum().sort_values(ascending=False).reset_index()
    result = grpSum.loc[:4, :]
    other = grpSum.loc[5:, '비중'].sum()
    if other > 0.1:
        tmp = pd.DataFrame({'업종명': '기타', '비중': other}, index=[0])
        result = pd.concat([result, tmp])

    return result.to_json(orient='split')

def standardize_price(data):
    _med = data.median()
    centered = data - _med

    _max = centered.max()
    _min = centered.min()

    _stdData = 2 * (centered - _min) / (_max - _min) - 1
    return round(_stdData * 100, 2)

def get_etf_telegram_data(db: Session = Depends(get_db), code: str = ""):
    try :
        q1 = f"""
        SELECT *
        FROM (
            SELECT
                stock_name
            FROM etf_base_table
            WHERE etf_code = :code
                and recent_ratio <> 0
            ORDER BY recent_ratio DESC
            )
        WHERE ROWNUM <= 5
        """
        stocks = pd.read_sql(q1, con = db.connection(), params = {'code' : code})['stock_name'].tolist()
        data = clean_telegram_data(stocks)
        return {'list': stocks,
                'data': data.reset_index(drop=True).to_json(orient='records')}
    except oracledb.DatabaseError as e:
        logger.error(f'[get_etf_telegram_data] Database operation failed: {e}')

def get_code_price_describe(db: Session = Depends(get_db), code: str = ""):
    try :
        tz = pytz.timezone('Asia/Seoul')
        now = datetime.now(tz)
        today = now.strftime('%Y-%m-%d')
        month_ago = now - timedelta(days=90)  # 사실은 3달 전
        month_ago = month_ago.strftime('%Y-%m-%d')

        price = fdr.DataReader(f"NAVER:{code}", start=month_ago, end=today).reset_index()
        price = price[['Date', 'Close']]
        price['Date'] = price['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))

        current = price['Close'][price['Date'].idxmax()]

        highest = price['Close'].max()
        highest_ratio = (highest / current - 1) * 100

        lowest = price['Close'].min()
        lowest_ratio = (lowest / current - 1) * -100

        return {
            'highest' : f"{highest:,.0f}",
            'highest_ratio' : f"{highest_ratio:.2f}",
            'lowest' : f"{lowest:,.0f}",
            'lowest_ratio' : f"{lowest_ratio:.2f}",
        }
    except oracledb.DatabaseError as e:
        logger.error(f'[get_code_price_describe]Database operation failed: {e}')