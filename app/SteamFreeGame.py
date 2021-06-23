# author: luoxuan
# coding: utf-8
import re
import traceback

from flask import Flask
from flask import request
from flask import make_response
import urllib.parse
import requests
from requests_html import HTMLSession
from bs4.element import Tag
from bs4 import BeautifulSoup
import urllib3
from config import STEAM_URL, GET_LICENSES_URL, DELIVERY_AREA, GAME_APP_ID

app = Flask(__name__)

GAME_URL = ""
GAME_Packet_ID = ""

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def proxy_pass_request(redirect_url, request_method, request_params):

    session = HTMLSession()
    response = session.request(
        request_method,
        redirect_url,
        verify=False,
        # stream=True,
        headers=request_params['headers']
    )

    return response

# 判断游戏是否领取


def check_should_delivery_game(account_id, delivery_area, game_app_id, request_params):
    if int(account_id) <= 0:
        return False
    get_params = {
        'id': account_id,
        'cc': delivery_area
    }
    response = requests.request(
        'GET',
        GET_LICENSES_URL,
        headers=request_params.get('headers', {}),
        params=get_params)
    if response.status_code != 200:
        return False
    licence_info = response.json()
    if int(game_app_id) not in licence_info['rgOwnedPackages']:
        return True
    else:
        return False

# 合成领取脚本


def generate_delivery_game_script(delivery, delivery_area, session_id, game_app_id):
    if delivery:
        origin_js = """jQuery.ajax({
            url: '/account/setcountry',
            data: {
                sessionid: '%s',
                cc: '%s'
            },
            async: false,
            type: 'POST',
            success: function() {
                jQuery.post('/checkout/addfreelicense', {
                    action: 'add_to_cart',
                    sessionid: '%s',
                    subid: '%s'
                });
                window.location.href = window.location.href;
            }
        })""" % (
            session_id,
            delivery_area,
            session_id,
            game_app_id
        )

    else:
        origin_js = """jQuery.ajax({
            url: '/account/setcountry',
            data: {
                sessionid: '%s',
                cc: '%s'
            },
            async: false,
            type: 'POST'
        })""" % (
            session_id,
            delivery_area
        )
    return origin_js

# 获取 SessionID 和 AccountID


def get_steam_params_from_response(response_content):
    """
        var g_AccountID = 86433468;
            var g_sessionID = "32ef6dfb0621ece4f257501d";
            var g_ServerTime = 1624366269;
    """
    session_id_str = re.search(r'var g_sessionID = "(\w+?)";',
                               response_content)
    if not session_id_str:
        return False

    account_id_str = re.search(r'var g_AccountID = (\w+?);',
                               response_content)

    if not account_id_str:
        return False

    session_id = session_id_str.groups()[0]
    account_id = account_id_str.groups()[0]
    return {
        'session_id': session_id,
        'account_id': account_id,
    }

# 注入 Script 脚本


def insert_scripts_to_response_content(response_content, scripts):
    bs_obj = BeautifulSoup(response_content)
    script_tag = Tag(name='script')
    script_tag.string = scripts
    bs_obj.head.append(script_tag)
    return str(bs_obj)


def data_deal(request_params):
    proxy_result = proxy_pass_request(GAME_URL, 'GET', request_params)
    ignore_headers = ['Server', 'Content-Type',
                      'Content-Encoding', 'Connection', 'Vary', 'Content-Length']
    try:
        if GAME_Packet_ID:
            if proxy_result.status_code == 200:
                steam_params = get_steam_params_from_response(
                    proxy_result.html.html)
                print(steam_params)
                if steam_params:
                    check_result = check_should_delivery_game(steam_params['account_id'],
                                                            DELIVERY_AREA,
                                                            GAME_Packet_ID,
                                                            request_params)
                    if check_result:
                        print('User needs to delivery game')
                    else:
                        print("User needs to change Country")
                    delivery_scripts = generate_delivery_game_script(check_result,
                                                                    DELIVERY_AREA,
                                                                    steam_params['session_id'],
                                                                    GAME_Packet_ID)
                    new_response = insert_scripts_to_response_content(proxy_result.html.html,
                                                                    delivery_scripts)

                    resp = make_response(new_response)
                    for item_key in proxy_result.headers:
                        if item_key not in ignore_headers:
                            resp.headers[item_key] = proxy_result.headers[item_key]
                    return resp, proxy_result.status_code

    except Exception as e:
        print(traceback.format_exc())
    resp = make_response(proxy_result.html.html)
    for item_key in proxy_result.headers:
        if item_key not in ignore_headers:
            resp.headers[item_key] = proxy_result.headers[item_key]
    return resp, proxy_result.status_code


def generate_format_cookies(origin_cookie_str):
    cookies = {}
    for item_cookie_pair in origin_cookie_str.split(';'):
        if item_cookie_pair:
            cookie_key, cookie_value = item_cookie_pair.split('=')
            cookies[cookie_key.lstrip()] = urllib.parse.unquote(cookie_value)
    return cookies


@app.route('/app/<gameid>/<gamename>/')
def get_with_gameid_and_gamename(gameid, gamename):
    global GAME_URL
    global GAME_Packet_ID
    GAME_URL = STEAM_URL + f"/app/{gameid}/{gamename}/"
    try:
        GAME_Packet_ID = GAME_APP_ID[gameid]
    except:
        GAME_Packet_ID = False
        print("Game not support")
    print('receive request')
    request_headers = dict(request.headers or {})
    request_params = dict(request.args or {})
    request_post_data = dict(request.form or {})
    request_json = dict(request.json or {})
    request_headers.pop('X-Real-Ip', '')
    request_headers.pop('X-Forwarded-For', '')
    request_headers.pop('Accept-Encoding', '')
    request_headers['Connection'] = 'keep-alive'
    request_cookies = request_headers.get('Cookie', '')
    formated_cookies = generate_format_cookies(request_cookies)
    headers = {}
    request_headers.get('Cookie') and headers.update(
        {'Cookie': request_headers.get('Cookie')})
    request_headers.get(
        'User-Agent') and headers.update({'User-Agent': request_headers.get('User-Agent')})
    request_headers.get('Accept') and headers.update(
        {'Accept': request_headers.get('Accept')})
    request_headers.get('Accept-Language') and headers.update(
        {'Accept-Language': request_headers.get('Accept-Language')})
    request_headers.get(
        'sec-ch-ua') and headers.update({'sec-ch-ua': request_headers.get('sec-ch-ua')})
    request_headers.get('sec-ch-ua-mobile') and headers.update(
        {'sec-ch-ua-mobile': request_headers.get('sec-ch-ua-mobile')})
    request_headers.get('Sec-Fetch-Dest') and headers.update(
        {'Sec-Fetch-Dest': request_headers.get('Sec-Fetch-Dest')})
    request_headers.get('Sec-Fetch-Mode') and headers.update(
        {'Sec-Fetch-Mode': request_headers.get('Sec-Fetch-Mode')})
    request_headers.get(
        'Sec-Fetch-User') and headers.update({'Sec-Fetch-User': 1})
    request_headers.get('Upgrade-Insecure-Requests') and headers.update(
        {'Upgrade-Insecure-Requests': request_headers.get('Upgrade-Insecure-Requests')})
    request_headers['Host'] = 'store.steampowered.com'

    request_params = {
        'data': request_post_data,
        'params': request_params,
        'json': request_json,
        'headers': request_headers,
        # 'cookies': formated_cookies
    }
    print('receive params %s' % request_params)
    return data_deal(request_params)

@app.route('/app/<gameid>/')
def get_with_gameid(gameid):
    global GAME_URL
    global GAME_Packet_ID
    GAME_URL = STEAM_URL + f"/app/{gameid}/"
    try:
        GAME_Packet_ID = GAME_APP_ID[gameid]
    except:
        GAME_Packet_ID = False
        print("Game not support")
    print('receive request')
    request_headers = dict(request.headers or {})
    request_params = dict(request.args or {})
    request_post_data = dict(request.form or {})
    request_json = dict(request.json or {})
    request_headers.pop('X-Real-Ip', '')
    request_headers.pop('X-Forwarded-For', '')
    request_headers.pop('Accept-Encoding', '')
    request_headers['Connection'] = 'keep-alive'
    request_cookies = request_headers.get('Cookie', '')
    formated_cookies = generate_format_cookies(request_cookies)
    headers = {}
    request_headers.get('Cookie') and headers.update(
        {'Cookie': request_headers.get('Cookie')})
    request_headers.get(
        'User-Agent') and headers.update({'User-Agent': request_headers.get('User-Agent')})
    request_headers.get('Accept') and headers.update(
        {'Accept': request_headers.get('Accept')})
    request_headers.get('Accept-Language') and headers.update(
        {'Accept-Language': request_headers.get('Accept-Language')})
    request_headers.get(
        'sec-ch-ua') and headers.update({'sec-ch-ua': request_headers.get('sec-ch-ua')})
    request_headers.get('sec-ch-ua-mobile') and headers.update(
        {'sec-ch-ua-mobile': request_headers.get('sec-ch-ua-mobile')})
    request_headers.get('Sec-Fetch-Dest') and headers.update(
        {'Sec-Fetch-Dest': request_headers.get('Sec-Fetch-Dest')})
    request_headers.get('Sec-Fetch-Mode') and headers.update(
        {'Sec-Fetch-Mode': request_headers.get('Sec-Fetch-Mode')})
    request_headers.get(
        'Sec-Fetch-User') and headers.update({'Sec-Fetch-User': 1})
    request_headers.get('Upgrade-Insecure-Requests') and headers.update(
        {'Upgrade-Insecure-Requests': request_headers.get('Upgrade-Insecure-Requests')})
    request_headers['Host'] = 'store.steampowered.com'

    request_params = {
        'data': request_post_data,
        'params': request_params,
        'json': request_json,
        'headers': request_headers,
        # 'cookies': formated_cookies
    }
    print('receive params %s' % request_params)
    return data_deal(request_params)

def test_render():
    headers = {'Host': 'store.steampowered.com', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Cache-Control': 'no-cache', 'Sec-Ch-Ua': '"Chromium";v="86", "\\"Not\\\\A;Brand";v="99", "Google Chrome";v="86"', 'Sec-Ch-Ua-Mobile': '?0', 'Upgrade-Insecure-Requests': '1',
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Sec-Fetch-Site': 'none', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-User': '?1', 'Sec-Fetch-Dest': 'document', 'Accept-Language': 'zh-CN,zh;q=0.9'}
    session = HTMLSession()
    resp = session.get(GAME_URL, headers=headers, verify=False)
    return resp


if __name__ == '__main__':
    print('start server')
    # test_render()
    app.run(host='0.0.0.0', port=8080, debug=False)
