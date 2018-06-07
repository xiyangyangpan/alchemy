# -*- coding: utf-8 -*-

# python3 library
import uuid
import json
import sys
import time
from mylog import logger
if sys.version_info.major == 2:
    import httplib, urllib
    httplib.HTTPSConnection.debuglevel = 5
elif sys.version_info.major == 3:
    import http.client
    http.client.HTTPSConnection.debuglevel = 5


# **********************************************
# *** Update or verify the following values. ***
# **********************************************

# Replace the subscriptionKey string value with your valid subscription key.
subscriptionKey = 'cc111593bd7543c295db4ebb3d7e5c95'

# URL
host = 'api.cognitive.microsofttranslator.com'
path = '/translate?api-version=3.0'

# Translate to Chinese
params = "&to=zh"

headers = {
    'Ocp-Apim-Subscription-Key': subscriptionKey,
    'Content-type': 'application/json',
    'X-ClientTraceId': str(uuid.uuid4())
}


# Description: translate english sentences into chinese sentences
# Input: original byte stream
#        feature flag: feature_flag
#        sleep seconds: sleep_seconds
# Output: chinese byte stream
def ms_translate(content_bytes, feature_flag=True, sleep_seconds=1):
    if not feature_flag:
        return content_bytes
    if sys.version_info.major == 2:
        content_text = content_bytes
    elif sys.version_info.major == 3:
        # bytes to str
        content_text = content_bytes

    if not content_text.strip('\n'):
        return ''
    logger.debug((content_text))
    time.sleep(sleep_seconds)

    request_body = [{
        'Text': content_text
    }]

    request_content = json.dumps(request_body, ensure_ascii=False).encode('utf-8')
    logger.debug(request_content)

    max_try_num = 1
    for tries in range(max_try_num):
        try:
            conn = None
            print(sys.version_info.major)
            if sys.version_info.major == 2:
                data = urllib.urlencode({'Text': "test"})
                # conn = httplib.HTTPConnection(host)
                # conn.set_debuglevel(1)
                # conn.request("POST", path + params, request_content[0], headers)
                import requests
                from urlparse import urljoin
                ms_host = 'http://' + host
                res = requests.post(urljoin(ms_host, path), headers=headers, json=request_body)
                print (res.text)
                return ""
            elif sys.version_info.major == 3:
                conn = http.client.HTTPSConnection(host)
                conn.set_debuglevel(1)
                conn.request("POST", path+params, request_content, headers)
            response = conn.getresponse()
            result = response.read()
            logger.debug(result)

            # Note: We convert result, which is JSON, to and from an object so we can pretty-print it.
            # We want to avoid escaping any Unicode characters that result contains. See:
            # https://stackoverflow.com/questions/18337407/saving-utf-8-texts-in-json-dumps-as-utf8-not-as-u-escape-sequence
            logger.debug(json.dumps(json.loads(result), indent=4, ensure_ascii=False))
            output = json.loads(result)
            output_text = output[0]['translations'][0]['text']
            logger.debug("translated result: %s" % output_text)
            return output_text
        except UnicodeEncodeError as e:
            logger.info(repr(content_text))
            logger.error(e)
            sys.exit(1)
        except Exception as e:
            logger.info(content_text)
            logger.error(e)
            if tries < max_try_num-1:
                time.sleep(15)
                continue
            else:
                raise e


if __name__ == '__main__':
    print(ms_translate(''))
    print(ms_translate('Shorts', True))
    #print(ms_translate('How much revenue AWS actually generated for Amazon had long been a source of speculation. Was the service, a cloud-based data management and storage service, even profitable?', True))
