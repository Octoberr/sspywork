"""
验证twitter的登陆是否有效
"""
import requests
url = '''https://api.twitter.com/1.1/followers/list.json?include_profile_interstitial_type=1&include_blocking=1&include_blocked_by=1&include_followed_by=1&include_want_retweets=1&include_mute_edge=1&include_can_dm=1&include_can_media_tag=1&skip_status=1&cursor=-1&user_id=988458200&count=20'''
res = requests.get(url)
