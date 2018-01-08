#!/usr/bin/python
# -*- coding:utf-8 -*-
from workflow import Workflow, web
import sys
import re
import json

ICON_DEFAULT = 'icon.png'

def get_res_tk(url):
    from lib import requests
    try:
        res = requests.get(url, timeout = 1.5)
        res.raise_for_status()
        return res
    except Exception:
        return res

def find_tkk_fn(res):
    re_tkk = r"TKK=eval\('(\(\(function\(\)\{.+?\}\)\(\)\))'\);"
    tkk_fn = re.search(re_tkk, res)
    return tkk_fn

def get_tkk():
    from lib import execjs
    url = 'https://translate.google.cn/'
    try:
        res = get_res_tk(url)
        tkk_fn = find_tkk_fn(res.text)
        content = tkk_fn.group(1).encode('utf-8').decode('unicode_escape')
        tkk = execjs.eval(content)
        return tkk
    except Exception:
        return None

# 获取需要验证的 ticket
def get_tk_request(text):
    from lib import execjs
    tkk = get_tkk()
    if tkk == None:
        return None
    ctx = execjs.compile("""
            function b(a, b) {
                for (var d = 0; d < b.length - 2; d += 3) {
                    var c = b.charAt(d + 2),
                        c = "a" <= c ? c.charCodeAt(0) - 87 : Number(c),
                        c = "+" == b.charAt(d + 1) ? a >>> c : a << c;
                    a = "+" == b.charAt(d) ? a + c & 4294967295 : a ^ c
                }
                return a
            }

            function tk(a,TKK) {
                for (var e = TKK.split("."), h = Number(e[0]) || 0, g = [], d = 0, f = 0; f < a.length; f++) {
                    var c = a.charCodeAt(f);
                    128 > c ? g[d++] = c : (2048 > c ? g[d++] = c >> 6 | 192 : (55296 == (c & 64512) && f + 1 < a.length && 56320 == (a.charCodeAt(f + 1) & 64512) ? (c = 65536 + ((c & 1023) << 10) + (a.charCodeAt(++f) & 1023), g[d++] = c >> 18 | 240, g[d++] = c >> 12 & 63 | 128) : g[d++] = c >> 12 | 224, g[d++] = c >> 6 & 63 | 128), g[d++] = c & 63 | 128)
                }
                a = h;
                for (d = 0; d < g.length; d++) a += g[d], a = b(a, "+-a^+6");
                a = b(a, "+-3^+b+-f");
                a ^= Number(e[1]) || 0;
                0 > a && (a = (a & 2147483647) + 2147483648);
                a %= 1E6;
                return a.toString() + "." + (a ^ h)
            }
        """)
    return ctx.call('tk', text, tkk)

headers = {
    'Host': 'translate.google.cn',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
    'Referer': 'https://translate.google.cn/',
    'Cookie': 'NID=101=pkAnwSBvDm2ACj2lEVnWO7YEPUoWCTges7B7z2jJNyrNwAZ2OL9FFOQLpdethA_20gCVqukiHnVm1hUbMGZc_ItQFdP5AHoq5XoMeEORaeidU196NDVRsrAu_zT0Yfsd; _ga=GA1.3.1338395464.1492313906',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0'
}

params = {
    'client': 't', 'sl': 'zh-CN', 'tl': 'en', 'hl': 'zh-CN',
    'dt': 'at', 'dt': 'bd', 'dt': 'ex', 'dt': 'ld', 'dt': 'md',
    'dt': 'qca', 'dt': 'rw', 'dt': 'rm', 'dt': 'ss', 'dt': 't',
    'ie': 'UTF-8', 'oe': 'UTF-8', 'source': 'bh', 'ssel': '0',
    'tsel': '0', 'kc': '1', 'tk': '376032.257956'
}

def get_res(url, data, params):
    from lib import requests
    try:
        res = requests.post(url, headers=headers, data=data, params=params, timeout=2)
        res.raise_for_status()
        return res
    except Exception as ex:
        return None


def parse_json(res):
    return json.loads(res)


def translate(text):
    global params

    url = 'https://translate.google.cn/translate_a/single'
    data = {'q': text}
    try:
        params['tk'] = get_tk_request(text)
        res = get_res(url, data, params)
        if res == None:
            return None
        ret_list = parse_json(res.text)
        return ret_list[0]
    except Exception as ex:
        return None

def main(wf):
    # workflow 写法导入第三方库文件，并且需要在 lib 下定义一个 __init__.py

    #input_content = sys.argv[1]
    input_content = "你是个好人"
    if input_content != "":
        res = translate(input_content)
        if res == None:
            translate_after_sentence = "ERROR"
            translate_before_sentence = "服务器出错，未成功翻译"
        else:
            # 翻译的内容可能是一篇文章（包含 \n ），所有这里需要遍历结果
            # 但使用 workflow 一般是翻译一句话和一个单词，因此只取第一个结果
            for item in res:
                translate_after_sentence = item[0]
                translate_before_sentence = item[1]
                break

    wf.add_item(title=translate_after_sentence,
                        subtitle=translate_before_sentence,
                        arg=translate_after_sentence,
                        valid=True,
                        icon=ICON_DEFAULT)

    wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow(libraries=['./lib'])
    logger = wf.logger
    sys.exit(wf.run(main))
