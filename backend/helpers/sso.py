import logging
import requests
from helpers.docdb import docDB

logger = logging.getLogger(__name__)


def nlpt_fetch_participant(token):
    logger.info(f'Fetching Participant with token: {"*" * (len(token) - 4)}{token[-4:]}')
    s = requests.Session()
    s.headers = {'Content-Type': 'application/json'}
    s.auth('Bearer', token)

    r = s.get(docDB.get_setting('sso_onboarding_url'))
    if r.status_code > 300:
        logger.error(f'Fetch-Request returend status code {r.status_code}:\n{r.text}')
        return None
    return r.json()
