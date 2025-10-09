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
    prefix="/Lab",
)

@router.get('/etface/content')
async def get_lab_content(db: Session = Depends(get_db), code: str = "") :
    try :
        low_PRB_high_ROE, high_Debt_high_ROE, high_quality, = await asyncio.gather(
            get_low_pbr_high_roe(db),
            get_high_debt_high_roe(db),
            get_high_quality(db)

        )
        return {
            "low_PRB_high_ROE" : low_PRB_high_ROE,
            "high_Debt_high_ROE" : high_Debt_high_ROE,
            "high_quality" : high_quality,
        }

    except Exception as e:

        print(f"ERROR : {e} | CODE : {code} | DOMAIN : lab_router")

        raise HTTPException(status_code=500, detail=str(e))

async def get_low_pbr_high_roe(db: Session = Depends(get_db)):
    try :
        code_table = pd.read_sql('select * from etf_info', con=db.connection())[['단축코드', '한글종목약명']]
        code_table.columns = ['ETF코드', 'ETF명']

        q = 'select * from fs_etf_ratio'
        ratio = pd.read_sql(q, con = db.connection())

        # PBR 1.0 미만, ROA 3.0% 이상
        con1 = ratio['pbr'] < 1.0
        con2 = ratio['ROA(총자산이익률, %)'] > 3.0
        ratio = ratio[con1 & con2].sort_values('ROA(총자산이익률, %)', ascending=False)[
            ['ETF코드', 'pbr', 'ROA(총자산이익률, %)', 'ROE(자기자본이익률, %)']]
        ratio = ratio.set_index('ETF코드').join(code_table.set_index('ETF코드'))
        ratio = ratio.reset_index(drop=True)
        ratio.columns = ['PBR', 'ROA(총자산이익률, %)', 'ROE(자기자본이익률, %)', 'ETF명']
        ratio = ratio[['ETF명', 'PBR', 'ROA(총자산이익률, %)', 'ROE(자기자본이익률, %)']]

        return {
            'low_PRB_high_ROE' : ratio.to_json(orient='split'),
        }
    except oracledb.DatabaseError as e:
        logger.error(f'[get_low_pbr_high_roe]Database operation failed: {e}')


async def get_high_debt_high_roe(db: Session = Depends(get_db)):
    try :
        code_table = pd.read_sql('select * from etf_info', con=db.connection())[['단축코드', '한글종목약명']]
        code_table.columns = ['ETF코드', 'ETF명']

        q = 'select * from fs_etf_ratio'
        ratio = pd.read_sql(q, con=db.connection())

        # 부채비율 300% 이상, ROE 6% 이상
        con1 = ratio['부채비율(%)'] > 300
        con2 = ratio['ROE(자기자본이익률, %)'] > 6.0
        ratio = ratio[con1 & con2].sort_values('ROA(총자산이익률, %)', ascending=False)[
            ['ETF코드', '부채비율(%)', 'ROA(총자산이익률, %)', 'ROE(자기자본이익률, %)']]
        ratio = ratio.set_index('ETF코드').join(code_table.set_index('ETF코드'))
        ratio = ratio.reset_index(drop=True)
        ratio.columns = ['부채비율(%)', 'ROA(총자산이익률, %)', 'ROE(자기자본이익률, %)', 'ETF명']
        ratio = ratio[['ETF명', '부채비율(%)', 'ROA(총자산이익률, %)', 'ROE(자기자본이익률, %)']]
        ratio = ratio.sort_values('ROE(자기자본이익률, %)', ascending=False)

        return {
            'high_Debt_high_ROE' : ratio.to_json(orient='split'),
        }
    except oracledb.DatabaseError as e:
        logger.error(f'[get_high_debt_high_roe]Database operation failed: {e}')


async def get_high_quality(db: Session = Depends(get_db)):
    try :
        code_table = pd.read_sql('select * from etf_info', con=db.connection())[['단축코드', '한글종목약명']]
        code_table.columns = ['ETF코드', 'ETF명']

        q = 'select * from fs_etf_ratio'
        ratio = pd.read_sql(q, con=db.connection())

        con1 = ratio['현금순환주기(CCC)'] < 60
        con2 = ratio['유동비율(%)'] > 150
        con3 = ratio['ROE(자기자본이익률, %)'] > 6

        ratio = ratio[con1 & con2 & con3].sort_values('ROE(자기자본이익률, %)', ascending=False)[
            ['ETF코드', 'ROE(자기자본이익률, %)', '현금순환주기(CCC)', '부채비율(%)']]
        ratio = ratio.set_index('ETF코드').join(code_table.set_index('ETF코드'))
        ratio = ratio.reset_index(drop=True)
        ratio.columns = ['ROE(자기자본이익률, %)', '현금순환주기(CCC)', '유동비율(%)', 'ETF명']
        ratio = ratio[['ETF명', 'ROE(자기자본이익률, %)', '현금순환주기(CCC)', '유동비율(%)']]

        return {
            'high_quality' : ratio.to_json(orient='split'),
        }
    except oracledb.DatabaseError as e:
        logger.error(f'[get_high_quality]Database operation failed: {e}')