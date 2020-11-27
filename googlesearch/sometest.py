from pathlib import Path

import random
USER_AGENT = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)'
try:
    try:
        user_agents_file = Path('user_agents.txt.gz')
        import gzip
        fp = gzip.open(user_agents_file.as_posix(), 'rb')
        try:
            user_agents_list = [_.strip() for _ in fp.readlines()]
        finally:
            fp.close()
            del fp
    except Exception:
        pass

except Exception:
    user_agents_list = [USER_AGENT]


def get_random_user_agent():
    """
    Get a random user agent string.

    :rtype: str
    :return: Random user agent string.
    """
    return random.choice(user_agents_list)


a = get_random_user_agent()
print(a.decode('utf-8'))