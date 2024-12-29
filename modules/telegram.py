import pandas as pd
import requests
from bs4 import BeautifulSoup
from config import *

def clean_telegram_data(stocks):
    data = pd.DataFrame({})
    for channel, url in telegramConfig.items():
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