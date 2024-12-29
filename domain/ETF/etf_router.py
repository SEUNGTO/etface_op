from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from config import *
import pandas as pd
import pytz
import json
from datetime import datetime, timedelta
import FinanceDataReader as fdr
from modules.telegram import *

router = APIRouter(
    prefix="/ETF",
)

@router.get("/{code}/top10")
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
        for _, item in data.iterrows():
            result[item['종목명']] = item['비중']

        return result

    except oracledb.DatabaseError as e:
        logger.error(f'[get_etf_data] Database operation failed: {e}')


@router.get("/{code}/similar")
def get_similar_etf_data(db: Session = Depends(get_db), code: str = ""):
    try :
        q1 = f"""
            SELECT etf_name, etf_code, stock_name, recent_ratio
            FROM etf_base_table
            WHERE 1 = 1
            and etf_code in (SELECT CAST("{code}" as VARCHAR(50)) FROM similar_etf)
            and recent_ratio <> 0
            """
        data = pd.read_sql(q1, con = db.connection())
        
        # subset_code = data['etf_code'].drop_duplicates().to_list()
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


@router.get('/{code}/depositDetail')
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


@router.get('/telegram/{code}')
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
@router.get('/{code}/price')
def get_code_price(db: Session = Depends(get_db), code: str = ""):
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
        q = f"""
        SELECT *
        FROM etf_target
        WHERE code = '{code}'
        """
        target = pd.read_sql(q, con = db.connection())
        target['target'] = standardize_price(target['target'])

        if target.shape[0] != 0:
            target = target.loc[target['code'] == code, ['Date', 'target']]
            price = price.merge(target, on='Date')

        else:
            price['target'] = None

        return price.to_dict()

    except oracledb.DatabaseError as e:
        logger.error(f'[get_code_price]Database operation failed: {e}')


@router.get('/{code}/price/describe')
def get_code_price_describe(db: Session = Depends(get_db), code: str = ""):
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



# def clean_telegram_data(stocks):
#     data = pd.DataFrame({})
#     for channel, url in telegramConfig.items():
#         for stock in stocks:
#             try:
#                 msg = telegram_crawller(url, stock)
#                 msg['시간'] = msg['일자'] + " " + msg['시간']
#                 msg.drop('일자', axis=1, inplace=True)
#                 msg['종목명'] = stock
#                 msg['채널명'] = channel
#                 msg = msg[['채널명', '종목명', '조회수', '링크', '시간', '메세지']]
#                 msg.reset_index(drop=True)
#                 data = pd.concat([data, msg])
#             except:
#                 continue
#     data = data.sort_values('시간', ascending=False)
#     return data

# def telegram_crawller(url, keyword):
#     telegram_msgs = {
#         'msg': []
#         , 'date': []
#         , 'time': []
#         , 'view': []
#         , 'link': []
#     }
#     query = f'{url}?q={keyword}'
#     response = requests.get(query)
#     soup = BeautifulSoup(response.content, 'html.parser')

#     for msg in soup.find_all('div', class_='tgme_widget_message_bubble'):

#         msg.find('a').decompose()
#         _view = msg.find('span', class_='tgme_widget_message_views').text

#         try:
#             _msg = msg.find('div', class_='tgme_widget_message_text js-message_text').text

#             datetime = pd.to_datetime(msg.find('time', class_='time').attrs['datetime'])
#             datetime = datetime.tz_convert('Asia/Seoul')
#             _date = datetime.strftime('%Y-%m-%d')
#             _time = datetime.strftime('%H:%M')

#             telegram_msgs['msg'].append(_msg)
#             telegram_msgs['date'].append(_date)
#             telegram_msgs['time'].append(_time)
#             telegram_msgs['view'].append(_view)

#         except:
#             _msg = None
#             telegram_msgs['msg'].append(_msg)
#             telegram_msgs['date'].append("-")
#             telegram_msgs['time'].append("-")
#             telegram_msgs['view'].append(_view)

#     for uu in soup.find_all('a', class_='tgme_widget_message_date'):
#         _link = uu.attrs['href']
#         telegram_msgs['link'].append(_link)

#     telegram_msgs = pd.DataFrame(telegram_msgs)
#     telegram_msgs.columns = ['메세지', '일자', '시간', '조회수', '링크']
#     telegram_msgs.sort_values(by=['일자', '시간'], ascending=[False, False], inplace=True)

#     return telegram_msgs.dropna()


def standardize_price(data):
    _med = data.median()
    centered = data - _med

    _max = centered.max()
    _min = centered.min()

    _stdData = 2 * (centered - _min) / (_max - _min) - 1
    return _stdData * 100


@router.get("/{code}/finance")
def get_etf_finance(db: Session = Depends(get_db), code: str = ""):

    try :
        query = f"""
            SELECT t1.acount_name, t1.amount, t2."CU수량"
            FROM (
                SELECT *
                FROM ETF_FINANCE
                WHERE etf_code = '{code}'
                ) t1
            LEFT JOIN (
                SELECT "CU수량", "단축코드"
                FROM etf_info
                WHERE "단축코드" = '{code}'
            ) t2
            on t1.etf_code = t2."단축코드"
        """
        data = pd.read_sql(query, con = db.connection())
        n_cu = data['CU수량'].to_list()[0]
        ratio = get_ratio(data, code, n_cu)

        data['amount'] = [f"{v:,.0f}" for v in data['amount']]
        data.drop('CU수량', axis = 1, inplace = True)
        data.columns = ['계정명', '금액']
        data['구분'] = data['계정명'].copy()
        data['구분'] = data['구분'].replace({
            '당기순이익' : '포괄손익',
            '매출액' : '포괄손익',
            '매출채권' : '자산',
            '부채총계' : '부채',
            '비유동부채' : '부채',
            '비유동자산' : '자산',
            '영업이익' : '포괄손익',
            '유동부채' : '부채',
            '유동자산' : '자산',
            '이익잉여금' : '자본',
            '자본총계' : '자본',
            '자산총계' : '자산',
            '재고자산' : '자산',
            '현금' : '자산'
        })
        data['순서'] = data['계정명'].copy()
        data['순서'] = data['순서'].replace({
            '매출액' : '01',
            '영업이익' : '02',
            '당기순이익' : '03',
            '현금' : '04',
            '매출채권' : '05',
            '재고자산' : '06',
            '유동자산' : '07',
            '비유동자산' : '08',
            '자산총계' : '09',
            '유동부채' : '10',
            '비유동부채' : '11',
            '부채총계' : '12',
            '이익잉여금' : '13',
            '자본총계' : '14',
        })
        
        return {
            'data' : data.sort_values('순서').to_json(orient='records'),
            'ratio' : ratio.to_json(orient = 'records')
            }
    except oracledb.DatabaseError as e:
        logger.error(f'[get_etf_finance] Database operation failed: {e}')

def get_ratio(data, code, n_cu) :
    data = data.set_index('acount_name')
    price = fdr.DataReader(code)['Close'].tail(1).values[0]
    ratio = [
        ['순이익률', data.loc['당기순이익', 'amount'] / data.loc['매출액', 'amount'] * 100],
        ['영업이익률', data.loc['영업이익', 'amount'] / data.loc['매출액', 'amount'] * 100],
        ['ROE(자기자본이익률)', data.loc['당기순이익', 'amount'] / data.loc['자본총계', 'amount'] * 100],
        ['ROA(총자산이익률)', data.loc['당기순이익', 'amount'] / data.loc['자산총계', 'amount'] * 100],
        ['부채비율', data.loc['부채총계', 'amount'] / data.loc['자본총계', 'amount'] * 100],
        ['유동비율', data.loc['유동자산', 'amount'] / data.loc['유동부채', 'amount'] * 100],
        ['EPS', data.loc['당기순이익', 'amount'] / n_cu],
        ['BPS', data.loc['자본총계', 'amount'] / n_cu],
        ['PER', price/(data.loc['당기순이익', 'amount'] / n_cu)],
        ['PBR', price/(data.loc['자본총계', 'amount'] / n_cu)],
    ]
    ratio = pd.DataFrame(ratio, columns = ['지표명', '값'])
    ratio['값'] = round(ratio['값'], 2)
    return ratio

@router.get("/{code}/profile")
def get_etf_profile(db: Session = Depends(get_db), code: str = ""):
    try : 
        tz = pytz.timezone('Asia/Seoul')
        now = datetime.now(tz)
        today = datetime(now.year, now.month, now.day)

        query = f"""
        SELECT "상장일", "기초지수명", "지수산출기관",
            "복제방법", "기초시장분류", "기초자산분류",
            "운용사", "CU수량", "총보수", "과세유형"
        FROM etf_info
        WHERE "단축코드" = '{code}'
        """
        data = pd.read_sql(query, con = db.connection())

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
        
        profile = {
            "운용사" : operator,
            '시장' : market,
            '기초자산' : asset,
            "스타일" : method,
            "산출기관" : tracker,
            "기초지수" : track_index,
            "상장일" : list_date.strftime("%Y년 %m월 %d일"),
            "상장일수" : days,
            '과세' : tax,
            '총보수' : pay,
            }

        return json.dumps(profile)

    except oracledb.DatabaseError as e:
        logger.error(f'[get_etf_data_by_order] Database operation failed: {e}')


@router.get("/{code}/{order}")
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
