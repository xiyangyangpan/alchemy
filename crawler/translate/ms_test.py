# -*- coding: utf-8 -*-

import uuid
import json
import sys
import time
import logging
from httplib import HTTPConnection
HTTPConnection.debuglevel = 5
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True


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
def ms_translate(content_text, feature_flag=True, sleep_seconds=1):
    if not content_text.strip('\n'):
        return ''

    request_body = [{
        'Text': content_text
    }]

    request_content = json.dumps(request_body, ensure_ascii=False).encode('utf-8')

    try:
            import requests
            from urlparse import urljoin
            ms_host = 'http://' + host
            res = requests.post(urljoin(ms_host, path), headers=headers, json=request_body)
            logging.debug( res.text)
            return ""

    except Exception as e:
            logging.error(e)


if __name__ == '__main__':
    print(ms_translate('Shorts Are Piling'))
