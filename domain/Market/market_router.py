import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from modules.telegram import *
import unicodedata

router = APIRouter(
    prefix="/market",
)

@router.get('/etface/content')
async def get_main_content(db: Session = Depends(get_db)) :
    try :
        industry, theme, industry_report, invest_info, calendar, category, daily_theme, daily_industry = await asyncio.gather(
            get_industry_label(db),
            get_theme_label(db),
            get_industry_report(db),
            get_invest_info(db),
            get_calendar(),
            get_category_table(db),
            get_daily_label(db, category='theme'),
            get_daily_label(db, category='industry')
        )

        return {
            "industry" : industry,
            "theme" : theme,
            "industry_report" : industry_report,
            "invest_info" : invest_info,
            "calendar" : calendar,
            "category" : category,
            "daily_theme" : daily_theme,
            "daily_industry" : daily_industry
        }

    except Exception as e:
        import pytz
        from datetime import datetime
        tz = pytz.timezone('Asia/Seoul')
        error = pd.DataFrame({'error' : e, 'code' : "", 'date' : datetime.now(tz).timestamp(),'domain' : 'market_router'})
        error.to_sql('error', con = db.connection(), if_exists='replace', index=False)

        raise HTTPException(status_code=500, detail=str(e))

async def get_industry_label(db: Session = Depends(get_db)):
    try:
        query = """
        SELECT "업종코드", "업종명", "종목코드", "종목명", "레이블", "업종점수", "업종레이블"
        FROM industry_label
        """
        industry = pd.read_sql(query, con = db.connection())
        industry = industry.drop_duplicates()
        industry.loc[:, '업종점수'] = round(industry.loc[:, '업종점수'] * 100, 2)
        industry = industry.sort_values('업종점수', ascending=False)
        industry.loc[:, '레이블'] = industry.loc[:, '레이블'].replace({
            '증권사의 관심을 받기 시작했어요.': '첫 관심🆕',
            '증권사의 관심에서 멀어졌어요.': '관심Out🔚',
            '증권사의 관심이 늘었어요.': '관심도 증가📈',
            '증권사의 관심이 줄었어요.': '관심도 감소📉',
            '여러 애널리스트들의 관심을 받고 있어요.': "애널리스트 최애",
            '목표가를 올린 증권사가 있어요.': "목표가 상향의견✨",
            '목표가를 내린 증권사가 있어요.': "목표가 하향의견💦",
            '목표가가 상향되었어요.': "목표가 상향📈",
            '목표가가 하향되었어요.': "목표가 하향📉",
            '목표가에 큰 변화는 없어요.': "목표가 중립💬",
            '목표가가 신고가를 경신했어요.': '목표가 신고가🔺',
            '가장 낮은 목표가가 제시됐어요.': '목표가 신저가🚧',
            '매도리포트가 나왔어요.': '매도리포트😨',
        })

        cnt = pd.read_sql('select * from wics', con=engine)['업종코드'].value_counts()
        industry = industry.set_index('업종코드').join(cnt).rename(columns={'count': '업종 내 종목수'})
        industry = industry.reset_index()
        industry = industry[['업종코드', '업종명', '업종 내 종목수', '종목명', '레이블', '업종점수', '업종레이블']]
        group_col = ['업종코드', '업종명', '업종 내 종목수', '종목명', '업종점수', '업종레이블']
        industry = industry.sort_values('레이블').groupby(group_col, as_index=False).agg({
            '레이블': lambda x: ", ".join(x)
        })
        industry = industry.sort_values('업종점수', ascending = False)

        result = {
            'summary': {
                '전체' : len(industry['업종명'].unique()),
                '긍정': len(industry.loc[industry['업종레이블'] == '긍정', '업종명'].unique()),
                '부정': len(industry.loc[industry['업종레이블'] == '부정', '업종명'].unique()),
            },
            'data': industry.reset_index(drop=True).to_json(orient='split')
        }

        return result

    except oracledb.DatabaseError as e:
        logger.error(f'[get_industry_label] Database operation failed: {e}')


async def get_theme_label(db: Session = Depends(get_db)):
    try:
        query = """
        SELECT "테마코드", "테마명", "종목코드", "종목명", "레이블", "테마점수", "테마레이블"
        FROM theme_label
        """
        theme = pd.read_sql(query, con=db.connection())
        theme = theme.drop_duplicates()
        theme.loc[:, '테마점수'] = round(theme.loc[:, '테마점수'] * 100, 2)
        theme = theme.sort_values('테마점수', ascending=False)
        theme.loc[:, '레이블'] = theme.loc[:, '레이블'].replace({
            '증권사의 관심을 받기 시작했어요.': '첫 관심🆕',
            '증권사의 관심에서 멀어졌어요.': '관심Out🔚',
            '증권사의 관심이 늘었어요.': '관심도 증가📈',
            '증권사의 관심이 줄었어요.': '관심도 감소📉',
            '여러 애널리스트들의 관심을 받고 있어요.': "애널리스트 최애",
            '목표가를 올린 증권사가 있어요.': "목표가 상향의견✨",
            '목표가를 내린 증권사가 있어요.': "목표가 하향의견💦",
            '목표가가 상향되었어요.': "목표가 상향📈",
            '목표가가 하향되었어요.': "목표가 하향📉",
            '목표가에 큰 변화는 없어요.': "목표가 중립💬",
            '목표가가 신고가를 경신했어요.': '목표가 신고가 🔺',
            '가장 낮은 목표가가 제시됐어요.': '목표가 신저가 🚧',
            '매도리포트가 나왔어요.': '매도리포트😨',
        })

        cnt = pd.read_sql('select "테마코드" from theme', con=engine)['테마코드'].value_counts()
        theme = theme.set_index('테마코드').join(cnt).rename(columns={'count': '테마 내 종목수'})
        theme = theme.reset_index()
        theme = theme[['테마코드', '테마명', '테마 내 종목수', '종목명', '레이블', '테마점수', '테마레이블']]
        group_col = ['테마코드', '테마명', '테마 내 종목수', '종목명', '테마점수', '테마레이블']
        theme = theme.sort_values('레이블').groupby(group_col, as_index=False).agg({
            '레이블': lambda x: ", ".join(x)
        })

        theme = theme.sort_values('테마점수', ascending=False)

        result = {
            'summary': {
                '전체': len(theme['테마명'].unique()),
                '긍정': len(theme.loc[theme['테마레이블'] == '긍정', '테마명'].unique()),
                '부정': len(theme.loc[theme['테마레이블'] == '부정', '테마명'].unique()),
            },
            'data': theme.reset_index(drop=True).to_json(orient='split')
        }

        return result

    except oracledb.DatabaseError as e:
        logger.error(f'[get_industry_label] Database operation failed: {e}')


async def get_industry_report(db: Session = Depends(get_db)):
    try:
        query = """
        SELECT "산업", "제목", "증권사", "게시일자", "링크", "다운로드"
        FROM industry_report
        """
        report = pd.read_sql(query, con=db.connection())
        report = report.sort_values('게시일자', ascending=False)


        return report.reset_index(drop=True).to_json(orient='split')

    except oracledb.DatabaseError as e:
        logger.error(f'[get_industry_report] Database operation failed: {e}')


async def get_invest_info(db: Session = Depends(get_db)):
    try:
        query = """
        SELECT "제목", "증권사", "게시일자", "링크", "다운로드"
        FROM invest_info
        """
        report = pd.read_sql(query, con=db.connection())
        report = report.sort_values('게시일자', ascending=False)

        return report.reset_index(drop=True).to_json(orient='split')

    except oracledb.DatabaseError as e:
        logger.error(f'[get_invest_info] Database operation failed: {e}')

async def get_calendar():
    try :
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
        data = data[['지표명', '국가', '날짜', '시간', '이전 실적', '이번 예상', '실제 실적', '중요도']]

        # 2024-11-26 중요도 데이터가 바뀌어서 수정함
        data['중요도'] = data['중요도'].apply(lambda x: x.split("_")[-1])
        data['중요도'] = data['중요도'].str.replace("high", "⬛⬛⬛")
        data['중요도'] = data['중요도'].str.replace("md", "⬛⬛⬜")
        data['중요도'] = data['중요도'].str.replace("low", "⬛⬜⬜")

        # 전처리 : 엔 표기 변경
        data[['이전 실적', '이번 예상', '실제 실적']] = data[['이전 실적', '이번 예상', '실제 실적']].apply(lambda x: x.str.replace("&yen;", "￥"))

        # 데이터 정렬
        data = data.sort_values(['날짜', '시간'])

        return data.reset_index(drop=True).to_json(orient='split')

    except oracledb.DatabaseError as e:
        logger.error(f'[get_active_etf_dropitem] Database operation failed: {e}')


async def get_category_table(db: Session = Depends(get_db)) :
    industry = pd.read_sql('SELECT DISTINCT TO_CHAR("업종명") AS name FROM wics', con=db.connection())
    industry = industry['name'].to_list()
    theme = pd.read_sql('SELECT DISTINCT TO_CHAR("테마명") AS name FROM theme', con=db.connection())
    theme = theme['name'].to_list()

    return {
        'theme' : theme,
        'industry' : industry,
    }

@router.get('/{category}/{name}')
async def get_daily_label(db: Session = Depends(get_db), category:str = "", name:str = "") :
    try :
        data = pd.DataFrame()


        if category == 'theme':
            if name == "":
                q = """
                SELECT "테마명"
                FROM theme_label_daily
                WHERE TO_NUMBER("테마점수") = (
                    SELECT MAX(TO_NUMBER("테마점수")) FROM theme_label_daily
                )
                AND ROWNUM <= 1
                """
                name_df = pd.read_sql(q, con=db.connection())
                name = name_df['테마명'].values[0]

            q = f"""
                SELECT DISTINCT TO_CHAR("날짜"), TO_NUMBER("테마점수") * 100
                FROM theme_label_daily
                WHERE TO_CHAR("테마명") = :name
                ORDER BY TO_CHAR("날짜")
            """

            data = pd.read_sql(q, con=db.connection(), params={"name": name})

        elif category == 'industry':
            if name == "" :
                q = """
                SELECT "업종명"
                FROM industry_label_daily
                WHERE TO_NUMBER("업종점수") = (
                    SELECT MAX(TO_NUMBER("업종점수")) FROM industry_label_daily
                )
                AND ROWNUM <= 1
                """
                name_df = pd.read_sql(q, con=db.connection())
                name = name_df['업종명'].values[0]

            q = """
                SELECT DISTINCT TO_CHAR("날짜"), TO_NUMBER("업종점수") * 100
                FROM industry_label_daily
                WHERE TO_CHAR("업종명") = :name
                ORDER BY TO_CHAR("날짜")
            """

            data = pd.read_sql(q, con=db.connection(), params={"name": name})

        data.columns = ['date', 'score']
        data['date'] = pd.to_datetime(data['date'], errors='coerce')
        data['score'] = round(data['score'], 2)
        data = data.dropna(subset=['date'])

        if data.empty:
            return {
                'name': name,
                'date': [],
                'score': [],
                'target': []
            }

        date_range = pd.date_range(start=data['date'].min(), end=data['date'].max())
        result = pd.DataFrame(index=date_range)
        result = result.join(data.set_index('date')).ffill().reset_index(names='date')
        result['date'] = result['date'].dt.strftime('%Y-%m-%d')
        result['target'] = None

        return {
            'name': name,
            'date': result['date'].to_list(),
            'score': result['score'].to_list(),
            'target': result['target'].to_list()
        }
    except :
        return {
            'name' : name,
            'date' : None,
            'score' : None,
            'target' : None
        }


def normalize_name(value: str) -> str:
    if value is None:
        return ""
    # 유니코드 통일 → 앞뒤 공백 제거 → 대문자 변환
    return unicodedata.normalize('NFKC', value).strip()
