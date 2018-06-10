#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import sys
import hashlib
import urllib
import random
import json
from ts_log import logger
from Translator import Translator
if sys.version_info.major == 2:
    import httplib
elif sys.version_info.major == 3:
    import http.client


class BaiduTranslator(Translator):
    def translate(self, text):
        return baidu_translate(text)


# Description: translate english sentences into chinese sentences
# Input: original byte stream
#        feature flag: feature_flag
#        sleep seconds: sleep_seconds
# Output: chinese byte stream
def baidu_translate(content_bytes, feature_flag=True, sleep_seconds=2):
    if not feature_flag:
        return content_bytes

    if sys.version_info.major == 2:
        content = content_bytes
    elif sys.version_info.major == 3:
        # bytes to str
        content = str(content_bytes, encoding="utf-8")

    if not content.strip('\n').strip():
        return ''
    logger.debug(repr(content))
    time.sleep(sleep_seconds)

    http_conn = None
    max_try_num = 10
    for tries in range(max_try_num):
        try:
            appid = '20151113000005349'
            secretKey = 'osubCEzlGjzvw8qdQc41'
            q = content
            if sys.version_info.major == 2:
                quote_content = urllib.quote(content)
            elif sys.version_info.major == 3:
                quote_content = urllib.parse.quote(content)

            salt = random.randint(32768, 65536)
            sign = appid + q + str(salt) + secretKey
            m1 = hashlib.md5()
            m1.update(sign.encode("utf-8"))
            sign = m1.hexdigest()
            fy_url = '/api/trans/vip/translate'
            fy_url = fy_url + '?appid=' + appid + '&q=' + quote_content \
                + '&from=en' + '&to=zh' + '&salt=' + str(salt) + '&sign=' + sign

            if sys.version_info.major == 2:
                http_conn = httplib.HTTPConnection('api.fanyi.baidu.com')
            if sys.version_info.major == 3:
                http_conn = http.client.HTTPConnection('api.fanyi.baidu.com')
            http_conn.request('GET', fy_url)

            # response是HTTPResponse对象
            response = http_conn.getresponse()
            result = json.loads(response.read().decode('utf-8'))
            # logger.debug(result)
            out_text = result['trans_result'][0]['dst']
            logger.debug("translated result: %s" % out_text)
            return out_text
        except UnicodeEncodeError as e:
            logger.info(repr(content))
            logger.error(e)
            sys.exit(1)
        except Exception as e:
            logger.info(content)
            logger.error(e)
            if http_conn:
                http_conn.close()
            if tries < max_try_num-1:
                time.sleep(15)
                continue
            else:
                raise e


if __name__ == '__main__':
    print(baidu_translate(''))
    print(baidu_translate(b'Shorts Are Piling Into These Stocks. Should You Be Worried?', True))
    print(baidu_translate(b'How much revenue AWS actually generated for Amazon had long been a source of speculation. Was the service, a cloud-based data management and storage service, even profitable?', True))
