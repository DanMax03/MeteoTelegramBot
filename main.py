import super_secret
from telebot.async_telebot import AsyncTeleBot
from bs4 import BeautifulSoup
import asyncio
import requests_async as requests
import math


bot = AsyncTeleBot(super_secret.bot_key)

start_message = 'Привет! Я - метеологический бот, который позволяет получать ' \
                'информацию о погоде сегодня, завтра, на неделю вперёд.'

help_message = '''
Чтобы воспользоваться ботом, напишите запрос в следующем формате:
*Название_города < / температура / осадки / влажность> <сегодня / завтра>*
Примеры:
- *Москва сегодня* - вернёт все вышеупомянутые характеристики для Москвы на сегодняшний день
- *Мюнхен температура завтра* - вернёт прогноз температуры в Мюнхене на завтрашний день
- *Лондон осадки завтра* - вернёт прогноз по осадкам в Лондоне завтра
На данный момент бот собирает информацию на следующих ресурсах:
- gismeteo
'''

wrong_request_message = '''
Упс, вы ввели некорректную команду. Попробуйте снова.
Если вы забыли, как со мной работать, то воспользуйтесь командой */help*.
'''

error_message = '''
Запрос не удался :(
Возможно, меня уже забанил Gismeteo...
'''

user_agent_str = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 ' \
                 'Safari/537.36 '

measurements = ['температура', 'осадки', 'влажность']
dates = ['сегодня', 'завтра']

gismeteo_url = 'https://gismeteo.ru'


def is_correct_message(message):
    arr = message.text.split()
    if len(arr) < 2 or arr[-1] not in dates:
        return False
    return True


def city_div_searcher(tag):
    return tag.name == 'div' and 'catalog-subtitle' in tag.attrs['class'] and tag.text.startswith('Населённые')


def get_city(soup):
    link_tag = soup.find(city_div_searcher).next_sibling.div.a
    return gismeteo_url + link_tag.get('href'), link_tag.text


def get_meteo_info(soup):
    res = dict()

    block = soup.find('a', class_='weathertab weathertab-block tooltip')

    res['температура'] = 'от ' + ' до '.join(map(lambda x: x.text,
                                                 block.find_all('span', class_='unit unit_temperature_c')))

    res['осадки'] = block.get('data-text')

    humid_div = soup.find('div', class_='widget-row widget-row-humidity')
    humid_sum = 0
    cnt = 0
    for row in humid_div.children:
        humid_sum += int(row.text)
        cnt += 1
    res['влажность'] = str(math.floor(humid_sum / cnt)) + '%'

    return res


@bot.message_handler(commands=['start', 'help'])
async def handle_common_commands(message):
    if message.text == '/start':
        await bot.send_message(message.from_user.id, start_message)
    await bot.send_message(message.from_user.id, help_message, parse_mode='markdown')


@bot.message_handler(func=is_correct_message)
async def handle_user_request(message):
    arr = message.text.split()

    have_measurement = arr[-2] in measurements
    measurement = arr[-2] if have_measurement else None
    date = arr[-1]
    request_city_name_len = len(arr) - (2 if have_measurement else 1)
    request_city_name = ' '.join(arr[0:request_city_name_len])

    city_search_url = gismeteo_url + '/search/' + request_city_name
    search_soup = BeautifulSoup((await requests.get(city_search_url, headers={'user-agent': user_agent_str})).text,
                                'html.parser')

    final_link, final_city = get_city(search_soup)

    if final_city is None:
        await bot.send_message(message.from_user.id, error_message)

    final_soup = BeautifulSoup((await requests.get(final_link + ('/tomorrow' if date == 'завтра' else ''),
                               headers={'user-agent': user_agent_str})).text,
                               'html.parser')

    meteo_info = get_meteo_info(final_soup)

    s = 'Я смог найти запрос для города ' + final_city + ':\n'
    if measurement is None:
        s += 'Температура: ' + meteo_info['температура'] + '\n'
        s += 'Осадки: ' + meteo_info['осадки'] + '\n'
        s += 'Влажность: ' + meteo_info['влажность'] + '\n'
    elif measurement == 'температура':
        s += 'Температура: ' + meteo_info['температура'] + '\n'
    elif measurement == 'осадки':
        s += 'Осадки: ' + meteo_info['осадки'] + '\n'
    else:
        s += 'Влажность: ' + meteo_info['влажность'] + '\n'

    await bot.send_message(message.from_user.id, s)


@bot.message_handler()
async def handle_wrong_request(message):
    await bot.send_message(message.from_user.id, wrong_request_message)


if __name__ == '__main__':
    asyncio.run(bot.infinity_polling())
