import requests
from bs4 import BeautifulSoup
import browsercookie
import json
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
import ssl

import pprint
PPRINT = pprint.PrettyPrinter(indent=4)

DIFFICULTY_TYPES = ['Easy']

COOKIE_PATH = '/Users/jaypan/Library/Application Support/Google/Chrome/Profile 1/Cookies'
WEBSITE_URL = 'https://leetcode.com'

USER_AGENT_INFO = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) ' + \
                  'AppleWebKit/537.36 (KHTML, like Gecko) ' + \
                  'Chrome/63.0.3239.132 ' + \
                  'Safari/537.36'


class ForceTLSV1Adapter(HTTPAdapter):
    """Require TLSv1 for the connection"""
    def init_poolmanager(self, connections, maxsize, block=False):
        # This method gets called when there's no proxy.
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_version=ssl.PROTOCOL_TLSv1,
        )

    def proxy_manager_for(self, proxy, **proxy_kwargs):
        # This method is called when there is a proxy.
        proxy_kwargs['ssl_version'] = ssl.PROTOCOL_TLSv1
        return super(ForceTLSV1Adapter, self).proxy_manager_for(proxy, **proxy_kwargs)


def GetCookie(website_url, cookie_path):
    myNeedDomainDict = {}
    targetDomain = website_url.split('/')[-1]
    for _ in browsercookie.chrome([cookie_path]):
        if targetDomain in _.domain:
            myNeedDomainDict[_.name] = _.value
    return myNeedDomainDict


if __name__ == '__main__':
    with requests.Session() as s:
        s.mount(WEBSITE_URL, ForceTLSV1Adapter())
        s.cookies = requests.utils.cookiejar_from_dict(GetCookie(WEBSITE_URL, COOKIE_PATH))
        header = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'no-cache',
            'user-agent': USER_AGENT_INFO
        }
        r = s.get('https://leetcode.com/api/problems/all/')
        my_result = json.loads(r.text)
    my_statistic_data = {key: my_result[key] for key in ['ac_easy', 'ac_hard', 'ac_medium', 'num_solved']}
    my_quizs = []
    for my_quiz in my_result['stat_status_pairs']:
        quiz = {
            'frontend_question_id': int(my_quiz['stat']['frontend_question_id']),
            'question__title': my_quiz['stat']['question__title'],
            'status': my_quiz['status'],
            'paid_only': my_quiz['paid_only']
        }
        my_quizs.append(quiz)

    with open('Problems - LeetCode.html') as f:
        freq_lines = f.readlines()
    soup = BeautifulSoup('\n'.join(freq_lines), 'html.parser')
    trs = soup.select('tbody.reactable-data')[0].select('tr')
    freq_quiz = []
    for tr in trs:
        tds = tr.select('td')
        quiz = {
            'frontend_question_id': int(tds[1].text),
            'question__title': tds[2]['value'],
            'ac': float(tds[4]['value']),
            'level': tds[5].text,
            'frequency': float(tds[6]['value']),
            'href': tds[2].select('a')[0]['href']
        }
        freq_quiz.append(quiz)

    my_quizs_dict = {_['frontend_question_id']: _ for _ in my_quizs}
    freq_quiz_dict = {_['frontend_question_id']: _ for _ in freq_quiz}
    for k, v in freq_quiz_dict.items():
        my_quizs_dict[k].update(v)
    my_quizs = my_quizs_dict.values()

    try:
        with open('skip.json') as f:
            skip_questions = json.load(f)
    except:
        skip_questions = []

    data = sorted([_ for _ in my_quizs
                   if not _['paid_only'] and 'ac' != _['status'] and
                   _['frontend_question_id'] not in skip_questions and
                   'level' in _ and _['level'] in DIFFICULTY_TYPES],
                  key=lambda x: x['frequency'])

    PPRINT.pprint(data[-5:])
    print my_statistic_data
