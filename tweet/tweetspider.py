"""
twitter的爬虫
createby swm
2018/06/12
"""
import random
import requests
import json
import datetime
import uuid

from scrapy.selector import Selector

from writelog import WRITELOG
from conf import config


class TWEET:

    def __init__(self, keyword):
        self.usr = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36'
        self.url = "https://twitter.com/i/search/timeline?l=&q={}s&src=typed&max_position=%s".format(keyword)
        self.twitterfloder = config['twitterpath']
        # &f=tweets

    def getheaders(self):
        headers = {}
        headers['user-agent'] = self.usr
        headers['X-Forwarded-For'] = '%s.%s.%s.%s' % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        return headers

    def getrequestdata(self, url):
        """
        根据URL获取返回的数据然后做出判断
        :param url:
        :return:
        """
        headers = self.getheaders()
        try:
            res = requests.get(url, headers=headers)
            data = json.loads(res.text)
            return data
        except Exception as err2:
            WRITELOG().writelog('No data to jsonload,{}\n'.format(err2))
            return False

    def writeresdata(self, strtext):
        file = str(uuid.uuid1()) + '.twitter'
        filename = self.twitterfloder / file
        with open(filename, 'w', encoding='utf-8') as fp:
            fp.writelines(strtext)
        fp.close()
        return

    def parsepage(self, htmldata):
        page = Selector(text=htmldata)
        items = page.xpath('//li[@data-item-type="tweet"]/div')
        resdata = []
        for item in items:
            usernameTweet = item.xpath('.//span[@class="username u-dir u-textTruncate"]/b/text()').extract()[0]
            resdata.append('usernameTweet: {}\n'.format(usernameTweet))
            ID = item.xpath('.//@data-tweet-id').extract()
            if not ID:
                continue
            ID = ID[0]
            resdata.append('ID: {}\n'.format(ID))
            name = item.xpath('.//@data-name').extract()[0]
            resdata.append('name: {}\n'.format(name))
            screen_name = item.xpath('.//@data-screen-name').extract()[0]
            resdata.append('screen_name: {}\n'.format(screen_name))
            avatar = item.xpath('.//div[@class="content"]/div[@class="stream-item-header"]/a/img/@src').extract()[0]
            resdata.append('useravatar: {}\n'.format(avatar))
            # 获取twitter文本
            text = ' '.join(
                item.xpath('.//div[@class="js-tweet-text-container"]/p//text()').extract()).replace(' # ',
                                                                                                    '#').replace(
                ' @ ', '@')
            if text == '':
                # 没有twitter文本就直接跳过这个div
                continue
            resdata.append('text: {}\n'.format(text))
            usrurl = item.xpath('.//@data-permalink-path').extract()[0]
            resdata.append('usrurl: https://twitter.com{}\n'.format(usrurl))
            # nbr_retweet = item.css('span.ProfileTweet-action--retweet > span.ProfileTweet-actionCount').xpath(
            #     '@data-tweet-stat-count').extract()
            # if nbr_retweet:
            #     nbr_retweet = int(nbr_retweet[0])
            # else:
            #     nbr_retweet = 0
            # resdata.append('nbr_retweet: {}\n'.format(nbr_retweet))
            # nbr_favorite = item.css('span.ProfileTweet-action--favorite > span.ProfileTweet-actionCount').xpath(
            #     '@data-tweet-stat-count').extract()
            # if nbr_favorite:
            #     nbr_favorite = int(nbr_favorite[0])
            # else:
            #     nbr_favorite = 0
            # resdata.append('nbr_favorite: {}\n'.format(nbr_favorite))
            # nbr_reply = item.css('span.ProfileTweet-action--reply > span.ProfileTweet-actionCount').xpath(
            #     '@data-tweet-stat-count').extract()
            # if nbr_reply:
            #     nbr_reply = int(nbr_reply[0])
            # else:
            #     nbr_reply = 0
            # resdata.append('nbr_reply: {}\n'.format(nbr_reply))
            getdatetime = datetime.datetime.fromtimestamp(int(
                item.xpath('.//div[@class="stream-item-header"]/small[@class="time"]/a/span/@data-time').extract()[
                    0])).strftime('%Y-%m-%d %H:%M:%S')
            resdata.append('datetime: {}\n'.format(getdatetime))
            ### get photo
            has_cards = item.xpath('.//@data-card-type').extract()
            if has_cards and has_cards[0] == 'photo':
                has_image = True
                images = item.xpath('.//*/div/@data-image-url').extract()
                resdata.append('imgpath: {}\n'.format(images))
            elif has_cards:
                print('Not handle "data-card-type":\n%s' % item.xpath('.').extract()[0])
            ### get animated_gif
            has_cards = item.xpath('.//@data-card2-type').extract()
            if has_cards:
                if has_cards[0] == 'animated_gif':
                    has_video = True
                    videos = item.xpath('.//*/source/@video-src').extract()
                    resdata.append('videos: {}\n'.format(videos))
                elif has_cards[0] == 'player':
                    has_media = True
                    medias = item.xpath('.//*/div/@data-card-url').extract()
                    resdata.append('medias: {}\n'.format(medias))
                elif has_cards[0] == 'summary_large_image':
                    has_media = True
                    medias = item.xpath('.//*/div/@data-card-url').extract()
                    resdata.append('medias: {}\n'.format(medias))
                elif has_cards[0] == 'amplify':
                    has_media = True
                    medias = item.xpath('.//*/div/@data-card-url').extract()
                    resdata.append('medias: {}\n'.format(medias))
                elif has_cards[0] == 'summary':
                    has_media = True
                    medias = item.xpath('.//*/div/@data-card-url').extract()
                    resdata.append('medias: {}\n'.format(medias))
                elif has_cards[0] == '__entity_video':
                    pass  # TODO
                    # tweet['has_media'] = True
                    # tweet['medias'] = item.xpath('.//*/div/@data-src').extract()
                else:  # there are many other types of card2 !!!!
                    print('Not handle "data-card2-type":\n%s' % item.xpath('.').extract()[0])

            is_reply = item.xpath('.//div[@class="ReplyingToContextBelowAuthor"]').extract()
            is_reply = is_reply != []
            resdata.append('is_reply: {}\n'.format(is_reply))

            is_retweet = item.xpath('.//span[@class="js-retweet-text"]').extract()
            is_retweet = is_retweet != []
            resdata.append('is_retweet: {}\n'.format(is_retweet))

            user_id = item.xpath('.//@data-user-id').extract()[0]
            resdata.append('user_id: {}\n'.format(user_id))
            resdata.append('\n')
        self.writeresdata(resdata)

    def startapp(self):
        firsturl = self.url % ''
        firstresdta = self.getrequestdata(firsturl)
        if firstresdta:
            htmlitems = firstresdta['items_html']
            self.parsepage(htmlitems)
        else:
            WRITELOG().writelog("No data to parser!")
            return False
        # 是否有下一页
        hasnextpage = firstresdta['has_more_items']
        # 下一页的索引
        min_position = firstresdta['min_position']
        while hasnextpage:
            url = self.url % min_position
            resdata = self.getrequestdata(url)
            if resdata:
                self.parsepage(resdata['items_html'])
            else:
                WRITELOG().writelog("something wrong when get this {} data!".format(url))
                return False
            hasnextpage = resdata['has_more_items']
            if hasnextpage:
                min_position = resdata['min_position']
            else:
                WRITELOG().writelog('No more data to get!')
                break
        return True

#
if __name__ == '__main__':
    t = TWEET('flash')
    t.startapp()





