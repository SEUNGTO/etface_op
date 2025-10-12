import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from modules.telegram import *

router = APIRouter(
    prefix="/main",
)
@router.get('/etface/codelist')
async def get_layout_content(db: Session = Depends(get_db)) :
    try :
        codelist, = await asyncio.gather(
            get_codelist(db),
        )

        return {
            "codelist" : codelist,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/etface/content')
async def get_main_content(db: Session = Depends(get_db)) :
    try :
        codelist, industry, theme, etf, newItem, dropItem, = await asyncio.gather(
            get_codelist(db),
            get_popular_industry(db),
            get_popular_theme(db),
            get_popular_etf(db),
            get_active_etf_newitem(db),
            get_active_etf_dropitem(db),
        )

        return {
            "codelist" : codelist,
            "industry" : industry,
            "theme" : theme,
            "etf" : etf,
            "newItem" : newItem,
            "dropItem" : dropItem,
        }

    except Exception as e:

        import pytz
        from datetime import datetime
        tz = pytz.timezone('Asia/Seoul')
        error = pd.DataFrame({'error' : e, 'code' : "", 'date' : datetime.now(tz).timestamp(),'domain' : 'home_router'})
        error.to_sql('error', con = db.connection(), if_exists='append', index=False)

        raise HTTPException(status_code=500, detail=str(e))



async def get_codelist(db: Session = Depends(get_db)) :

    data = pd.read_sql('SELECT * FROM code_list', con=db.connection())
    data['Type'] = data['Type'].str.lower()

    return data.reset_index(drop=True).to_json(orient='records')

async def get_popular_industry(db: Session = Depends(get_db)):
    try:
        query = """
        SELECT "업종명", "업종코드", "업종점수", "업종레이블" 
        FROM industry_label
        """
        industry = pd.read_sql(query, con = db.connection())
        industry = industry.drop_duplicates()
        industry.loc[:, '업종점수'] = round(industry.loc[:, '업종점수'] * 100, 2)
        industry = industry.sort_values('업종점수', ascending=False)

        result = {
            'summary': {
                '긍정': int((industry['업종레이블'] == '긍정').sum()),
                '부정': int((industry['업종레이블'] == '부정').sum()),
                '중립': int((industry['업종레이블'] == '중립').sum()),
            },
            'data': industry.reset_index(drop=True).to_json(orient='split')
        }

        return result

    except oracledb.DatabaseError as e:
        logger.error(f'[get_popular_industry] Database operation failed: {e}')

async def get_popular_theme(db: Session = Depends(get_db)):
    try:
        query = """
        SELECT "테마명", "테마코드", "테마점수", "테마레이블" 
        FROM theme_label
        """
        theme = pd.read_sql(query, con = db.connection())
        theme = theme.drop_duplicates()
        theme.loc[:, '테마점수'] = round(theme.loc[:, '테마점수'] * 100, 2)
        theme = theme.sort_values('테마점수', ascending=False)

        result = {
            'summary': {
                '긍정': int((theme['테마레이블'] == '긍정').sum()),
                '부정': int((theme['테마레이블'] == '부정').sum()),
                '중립': int((theme['테마레이블'] == '중립').sum()),
            },
            'data': theme.reset_index(drop=True).to_json(orient='split')
        }

        return result

    except oracledb.DatabaseError as e:
        logger.error(f'[get_popular_theme] Database operation failed: {e}')

async def get_popular_etf(db: Session = Depends(get_db)):
    try:
        query = """
        SELECT "ETF명", "ETF코드", "ETF점수", "ETF레이블" 
        FROM etf_label
        """
        etf = pd.read_sql(query, con = db.connection())
        etf = etf.drop_duplicates()
        etf.loc[:, 'ETF점수'] = round(etf.loc[:, 'ETF점수'] * 100, 2)
        etf = etf.sort_values('ETF점수', ascending=False)

        result = {
            'summary': {
                '긍정': int((etf['ETF레이블'] == '긍정').sum()),
                '부정': int((etf['ETF레이블'] == '부정').sum()),
                '중립': int((etf['ETF레이블'] == '중립').sum()),
            },
            'data': etf.reset_index(drop=True).to_json(orient='split')
        }

        return result

    except oracledb.DatabaseError as e:
        logger.error(f'[get_popular_etf] Database operation failed: {e}')


async def get_active_etf_newitem(db: Session = Depends(get_db)):
    try:
        q = f"""
        SELECT etf_code, etf_name, stock_code, stock_name, recent_quantity, recent_amount, recent_ratio
        FROM etf_base_table
        WHERE 1 = 1
        and recent_ratio <> 0
        and past_ratio = 0
        """

        data = pd.read_sql(q, con=db.connection())
        etf_info = pd.read_sql('select "단축코드", "복제방법" from etf_info', con=db.connection())

        data = data.set_index('etf_code').join(etf_info.set_index('단축코드'))
        data = data[data['복제방법'] == '실물(액티브)']
        data = data.reset_index()

        data = data.set_index('stock_code').join(data['stock_code'].value_counts())
        data = data.join(data.groupby('stock_code')['recent_amount'].sum(), rsuffix='_sum').rename(
            columns={'recent_amount_sum': 'total_amount_for_stock'})
        data = data.set_index('etf_code').join(data.groupby('etf_code')['recent_amount'].sum(),
                                               rsuffix='_total').rename(
            columns={'recent_amount_total': 'total_amount_in_etf'})
        data = data.join(data.groupby('etf_code')['etf_name'].count(), rsuffix='_count').rename(
            columns={'etf_name_count': 'count_change_stock'})

        data = data.sort_values('recent_amount', ascending=False)

        # summary 정보
        stock_cnt = data['count'].max()
        pop_stock = data.loc[data['count'] == stock_cnt, ['stock_name', 'total_amount_for_stock']].drop_duplicates()
        pop_stock.columns = ['종목명', '금액']

        etf_cnt = data['count_change_stock'].max()
        act_etf = data.loc[data['count_change_stock'] == etf_cnt, ['etf_name', 'total_amount_in_etf',
                                                                   'count_change_stock']].drop_duplicates()
        act_etf.columns = ['ETF명', '투입금액', '변경종목수']

        data = data[['etf_name', 'count_change_stock', 'stock_name', 'recent_ratio', 'recent_amount']]
        data.columns = ['ETF명', '변경종목수', '종목명', '비중', '금액', ]
        data = data.sort_values('비중', ascending=False)

        result = {
            'summary': {
                'stock': {
                    'cnt': int(stock_cnt) if pd.notna(stock_cnt) else 0,
                    'item': pop_stock.reset_index(drop=True).to_json(orient='records')
                },
                'etf': {
                    'cnt': int(etf_cnt) if pd.notna(etf_cnt) else 0,
                    'item': act_etf.reset_index(drop=True).to_json(orient='records')
                }
            },
            'data': data.reset_index(drop=True).to_json(orient='split')
        }
        return result

    except oracledb.DatabaseError as e:
        logger.error(f'[get_active_etf_newitem] Database operation failed: {e}')


async def get_active_etf_dropitem(db: Session = Depends(get_db)):
    try:
        q = f"""
        SELECT etf_code, etf_name, stock_code, stock_name, past_quantity, past_amount, past_ratio
        FROM etf_base_table
        WHERE 1 = 1 
        and recent_ratio = 0
        and past_ratio <> 0
        """

        data = pd.read_sql(q, con=db.connection())
        etf_info = pd.read_sql('select "단축코드", "복제방법" from etf_info', con=db.connection())

        data = data.set_index('etf_code').join(etf_info.set_index('단축코드'))
        data = data[data['복제방법'] == '실물(액티브)']
        data = data.reset_index()

        data = data.set_index('stock_code').join(data['stock_code'].value_counts())
        data = data.join(data.groupby('stock_code')['past_amount'].sum(), rsuffix='_sum').rename(
            columns={'past_amount_sum': 'total_amount_for_stock'})
        data = data.set_index('etf_code').join(data.groupby('etf_code')['past_amount'].sum(),
                                               rsuffix='_total').rename(
            columns={'past_amount_total': 'total_amount_in_etf'})
        data = data.join(data.groupby('etf_code')['etf_name'].count(), rsuffix='_count').rename(
            columns={'etf_name_count': 'count_change_stock'})

        data = data.sort_values('past_amount', ascending=False)

        # summary 정보
        stock_cnt = data['count'].max()
        pop_stock = data.loc[data['count'] == stock_cnt, ['stock_name', 'total_amount_for_stock']].drop_duplicates()
        pop_stock.columns = ['종목명', '금액']

        etf_cnt = data['count_change_stock'].max()
        act_etf = data.loc[data['count_change_stock'] == etf_cnt, ['etf_name', 'total_amount_in_etf',
                                                                   'count_change_stock']].drop_duplicates()
        act_etf.columns = ['ETF명', '투입금액', '변경종목수']

        data = data[['etf_name', 'count_change_stock','stock_name', 'past_ratio', 'past_amount']]
        data.columns = ['ETF명', '변경종목수', '종목명', '비중', '금액', ]
        data = data.sort_values('비중', ascending=False)

        result = {
            'summary': {
                'stock': {
                    'cnt': int(stock_cnt) if pd.notna(stock_cnt) else 0,
                    'item': pop_stock.reset_index(drop=True).to_json(orient='records')
                },
                'etf': {
                    'cnt': int(etf_cnt) if pd.notna(etf_cnt) else 0,
                    'item': act_etf.reset_index(drop=True).to_json(orient='records')
                }
            },
            'data': data.reset_index(drop=True).to_json(orient='split')
        }
        return result

    except oracledb.DatabaseError as e:
        logger.error(f'[get_active_etf_dropitem] Database operation failed: {e}')