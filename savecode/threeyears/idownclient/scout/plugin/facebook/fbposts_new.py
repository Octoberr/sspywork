"""facebook get posts"""

# -*- coding:utf-8 -*-

import datetime
import json
import re
import time
import traceback
from urllib import parse
import threading
import random

from commonbaby.helpers import helper_str, helper_time
from lxml import etree

from datacontract.iscoutdataset import IscoutTask

from ....clientdatafeedback.scoutdatafeedback import (EResourceType,
                                                      NetworkPost,
                                                      NetworkProfile,
                                                      NetworkResource)
from .fbcontacts_new import FBContacts_new


class FBPosts_new(FBContacts_new):
    """get fb posts"""
    # https://scontent-lax3-1.xx.fbcdn.net/v/t1.0-0/p526x296/69804278_111868563515833_4365636361470869504_o.jpg?_nc_cat=111&_nc_oc=AQnj4Ka86udFWxRClRIoRuUr7zSwr4Rv6v0kCkGrpASpoYHJCxjt8Ws2jy4S2lJtik0&_nc_ht=scontent-lax3-1.xx&oh=98af744837c171e612e99d423d3c8a8f&oe=5E30E27C
    _re_rsc_name = re.compile(r'/([^/]+?)(\?|$)', re.S)

    def __init__(self, task: IscoutTask):
        super(FBPosts_new, self).__init__(task)

    def _get_posts_by_userid_v1(self,
                                task: IscoutTask,
                                userid: str,
                                reason: str = None,
                                timerange: int = 30) -> iter:
        """get fb posts by userid"""
        try:
            hostuser: NetworkProfile = self._get_user_by_userid_v1(userid)
            if not isinstance(hostuser, NetworkProfile):
                return

            for post in self._get_posts_v1(task,
                                           hostuser,
                                           reason,
                                           timerange=timerange):
                yield post

        except Exception as ex:
            self._logger.error("Get Posts by userid error: {}".format(ex.args))

    def _get_posts_by_url_v1(self,
                          task: IscoutTask,
                          userurl: str,
                          reason: str = None,
                          timerange: int = 30) -> iter:
        """get fb posts by user url"""
        try:
            hostuser: NetworkProfile = self._get_user_by_url_v1(userurl)
            if not isinstance(hostuser, NetworkProfile):
                return

            for post in self._get_posts_v1(task,
                                           hostuser,
                                           reason,
                                           timerange=timerange):
                yield post

        except Exception as ex:
            self._logger.error("Get Posts by userurl error: {}".format(
                ex.args))

    def _get_posts_v1(self,
                      task: IscoutTask,
                      hostuser: NetworkProfile,
                      reason: str = None,
                      timerange: int = 30) -> iter:
        """
        get fb posts by user profile
        所有推文的id都是取的feedback中的id,方便发送请求
        """
        try:
            if not isinstance(hostuser, NetworkProfile):
                self._logger.error("Invalid hostuser for getting Posts")
                return

            if hostuser.url is None or hostuser.url == "":
                hostuser.url = 'https://www.facebook.com/profile.php?id={}'.format(
                    hostuser._userid)


            docid_dict = self._get_docid_dict()
            if docid_dict == {} or docid_dict is None:
                self._logger.error("Get docid failed")
                return
            cursor = ''
            has_next_page: bool = True
            totalcount = 0
            while has_next_page:
                has_next_page = False
                url = 'https://www.facebook.com/api/graphql/'
                variables = '{' + f'"UFI2CommentsProvider_commentsKey":"ProfileCometTimelineRoute","afterTime":null,"beforeTime":null,"count":3,"cursor":"{cursor}","displayCommentsContextEnableComment":null,"displayCommentsContextIsAdPreview":null,"displayCommentsContextIsAggregatedShare":null,"displayCommentsContextIsStorySet":null,"displayCommentsFeedbackContext":null,"feedLocation":"TIMELINE","feedbackSource":0,"focusCommentID":null,"memorializedSplitTimeFilter":null,"omitPinnedPost":true,"postedBy":null,"privacy":null,"privacySelectorRenderLocation":"COMET_STREAM","renderLocation":"timeline","scale":1,"should_show_profile_pinned_post":true,"taggedInOnly":null,"useDefaultActor":false,"id":"{hostuser._userid}"' + '}'
                postdata = f'av={self._userid}&__user={self._userid}&__a=1&__csr=&__beoa=0&__pc={parse.quote(self._pc)}&dpr=1&__ccg=EXCELLENT&__hsi={self.hsi}&__comet_req=1&fb_dtsg={parse.quote(self.fb_dtsg)}&jazoest={self.jazoest}&__spin_r={self._spin_r}&__spin_b={self._spin_b}&__spin_t={self._spin_t}&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=ProfileCometTimelineFeedRefetchQuery&variables=' + parse.quote(
                    variables) + f'&doc_id={docid_dict["ProfileCometTimelineFeedRefetchQuery"]}'
                html = self._ha.getstring(url, postdata,
                                          headers="""
                            accept: */*
                            accept-encoding: gzip, deflate
                            accept-language: en-US,en;q=0.9,zh;q=0.8
                            content-length: {}
                            content-type: application/x-www-form-urlencoded
                            origin: https://www.facebook.com
                            referer: {}
                            sec-fetch-dest: empty
                            sec-fetch-mode: cors
                            sec-fetch-site: same-origin
                            user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36
                            """.format(len(postdata), hostuser.url))
                resp_infos = html.splitlines()
                for info in resp_infos:
                    jnode = None
                    json_info = json.loads(info)
                    # 第一条数据没有label
                    if 'label' not in json_info:
                        if not 'node' in json_info['data']:
                            if not 'timeline_list_feed_units' in json_info['data']['node']:
                                if not 'edges' in json_info['data']['node']['timeline_list_feed_units']:
                                    if not 'node' in json_info['data']['node']['timeline_list_feed_units']['edges']:
                                        continue
                        edges = json_info['data']['node']['timeline_list_feed_units']['edges']
                        if not edges:
                            self._logger.info("User {}({}) has no posts".format(hostuser.nickname, hostuser._userid))
                            break
                        jnode = json_info['data']['node']['timeline_list_feed_units']['edges'][0]['node']

                    else:
                        # 推文
                        if json_info['label'] == 'ProfileCometTimelineFeed_user$stream$ProfileCometTimelineFeed_user_timeline_list_feed_units':
                            if 'node' in json_info['data']:
                                jnode = json_info['data']['node']
                        # 是否有下一页
                        elif json_info['label'] == 'ProfileCometTimelineFeed_user$defer$ProfileCometTimelineFeed_user_timeline_list_feed_units$page_info':
                            if 'page_info' in json_info['data']:
                                has_next_page = json_info['data']['page_info']['has_next_page']
                                cursor = json_info['data']['page_info']['end_cursor']
                    if not jnode is None:
                        postid = helper_str.base64_decode(jnode['feedback']['id'])
                        post: NetworkPost = NetworkPost(postid, self._SOURCE, hostuser._userid)
                        post.nickname = hostuser.nickname
                        post.isroot = True

                        context_layout = jnode['comet_sections']['context_layout']
                        # 获取推文title
                        title = context_layout['story']['comet_sections']['title']
                        post.text = ''
                        if title['story'].__contains__('title'):
                            if not title['story']['title'] is None:
                                title_txt = title['story']['title']['text']
                                post.text = title_txt + '\n'
                        # 获取推文时间，判断是否在timerange范围内
                        timestamp = context_layout['story']['comet_sections']['timestamp']
                        if timestamp['story'].__contains__('backdated_time') and \
                                not timestamp['story']['backdated_time'] is None:
                            creation_time = timestamp['story']['backdated_time']['time']
                        else:
                            creation_time = timestamp['story']['creation_time']
                        dt_now = datetime.datetime.now()
                        dt_post = datetime.datetime.fromtimestamp(int(creation_time))
                        timedelta = dt_now - dt_post
                        post.posttime_datetime = dt_post
                        post.posttime = dt_post.strftime('%Y-%m-%d %H:%M:%S')
                        # 超过时间范围，直接返回
                        if timedelta.days > timerange:
                            return
                        # 获取推文url
                        post.posturl = timestamp['story']['url']

                        content = jnode['comet_sections']['content']
                        # 获取text
                        messages = content['story']['comet_sections']['message']
                        if not messages is None:
                            post.text += messages['story']['message']['text'] + '\n'

                        # 获取附加的视频，音频
                        attachments: list = content['story']['attachments']
                        for rsc in self._parse_post_attachments_v1(task, attachments, post, hostuser):
                            if not rsc is None:
                                yield rsc

                        # 分享的回忆
                        if attachments:
                            if 'attachment_target_renderer' in attachments[0]['style_type_renderer']:
                                target = attachments[0]['style_type_renderer']['attachment_target_renderer']['attachment']['target']
                                attachments = target['attachments']
                                # 分享回忆的附加资源
                                for rsc in self._parse_post_attachments_v1(task, attachments, post, hostuser):
                                    if not rsc is None:
                                        yield rsc
                                # 分享的回忆的文本内容（名字+时间+内容）
                                target_text = ''
                                target_text += target['comet_sections']['actor_photo']['story']['actors'][0]['name'] + '\t'
                                target_text += helper_time.timespan_to_datestr(target['comet_sections']['timestamp']['story']['creation_time']) + '\t'
                                if not target['message'] is None:
                                    target_text += target['message']['text']
                                post.text += target_text

                        # 转发的推文
                        attached_story = content['story']['comet_sections']['attached_story']
                        if not attached_story is None:
                            attached_story_layout = \
                            attached_story['story']['attached_story']['comet_sections']['attached_story_layout']
                            # 转发推文的附加资源
                            attachments: list = attached_story_layout['story']['attachments']
                            for rsc in self._parse_post_attachments_v1(task, attachments, post, hostuser):
                                if not rsc is None:
                                    yield rsc
                            # 转发推文文本内容（名字+时间+内容）
                            attached_story_text = ''
                            attached_story_info = attached_story_layout['story']['comet_sections']
                            attached_story_text += attached_story_info['title']['story']['actors'][0]['name'] + '\t'
                            attached_story_text += helper_time.timespan_to_datestr(attached_story_info['timestamp']['story']['creation_time']) + '\t'
                            if not attached_story_info['message']['story']['message'] is None:
                                attached_story_text += attached_story_info['message']['story']['message']['text']
                            post.text += attached_story_text

                        # feedback
                        feedback = jnode['comet_sections']['feedback']['story']['feedback_context']['feedback_target_with_context']
                        # 点赞人员拉取, comet_ufi_summary_and_actions_renderer是推文下面统计的那一行
                        post.likecount = feedback['comet_ufi_summary_and_actions_renderer']['feedback']['reaction_count']['count']
                        if post.likecount > 0:
                            self._get_post_likes_v1(post, hostuser)
                        # 评论部分
                        post.replycount = feedback['comment_count']['total_count']
                        yield post

                        totalcount += 1
                        self._logger.info(
                            "Got posts of [{}({})], {} posts found".format(hostuser.nickname, hostuser._userid, totalcount))

                        display_comments = feedback['display_comments']
                        for comment in self._parse_post_display_comments_v1(task, display_comments, post, hostuser):
                            if not comment is None:
                                yield comment

            self._logger.info(
                "Get user {}({}) post complete, {} posts found.".format(
                    hostuser.nickname, hostuser._userid, totalcount))

        except Exception:
            self._logger.error(
                "Get fb posts error:\nuserid={}\nusername={}\nerror:{}".format(
                    hostuser._userid, hostuser.nickname,
                    traceback.format_exc()))

    def _parse_post_display_comments_v1(self,
                                        task: IscoutTask,
                                        display_comments: dict,
                                        post: NetworkPost,
                                        hostuser: NetworkProfile) -> iter:
        """
        处理推文或评论的display_comments
        """
        try:
            # 先处理显示出来的评论
            edges: list = display_comments['edges']
            if len(edges) > 0:
                for comment in self._parse_post_edges_v1(task, edges, post, hostuser):
                    yield comment

            page_size = display_comments['page_size']
            after_count = display_comments['after_count']
            before_count = display_comments['before_count']
            end_cursor = display_comments['page_info']['end_cursor']
            if end_cursor is None:
                end_cursor = 'null'
            else:
                end_cursor = '"' + end_cursor + '"'
            has_next_page = display_comments['page_info']['has_next_page']
            has_previous_page = display_comments['page_info']['has_previous_page']
            start_cursor = display_comments['page_info']['start_cursor']
            if start_cursor is None:
                start_cursor = 'null'
            else:
                start_cursor = '"' + start_cursor + '"'
            url = 'https://www.facebook.com/api/graphql/'
            docid_dict = self._get_docid_dict()
            if docid_dict == {} or docid_dict is None:
                self._logger.error("Get docid failed")
                return
            postid_b64 = helper_str.base64str(post.postid)
            # 向下展开评论, before输入start_cursor, last输入min(before_count, pagesize), first和after为null
            while has_previous_page:
                # 每次请求间隔
                time.sleep(random.randint(0, 1))
                last = min(before_count, page_size)
                variables = '{' + f'"after":null,"before":{start_cursor},"displayCommentsFeedbackContext":null,"displayCommentsContextEnableComment":null,"displayCommentsContextIsAdPreview":null,"displayCommentsContextIsAggregatedShare":null,"displayCommentsContextIsStorySet":null,"feedLocation":"TIMELINE","feedbackID":"{postid_b64}","feedbackSource":0,"first":null,"focusCommentID":null,"includeHighlightedComments":false,"includeNestedComments":true,"isInitialFetch":false,"isPaginating":true,"last":{last},"scale":1,"topLevelViewOption":null,"useDefaultActor":false,"viewOption":null,"UFI2CommentsProvider_commentsKey":"ProfileCometTimelineRoute"' + '}'
                postdata = f'av={self._userid}&__user={self._userid}&__a=1&__csr=&__beoa=0&__pc={parse.quote(self._pc)}&dpr=1&__ccg=EXCELLENT&__hsi={self.hsi}&__comet_req=1&fb_dtsg={parse.quote(self.fb_dtsg)}&jazoest={self.jazoest}&__spin_r={self._spin_r}&__spin_b={self._spin_b}&__spin_t={self._spin_t}&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=CometUFICommentsProviderPaginationQuery&variables=' + parse.quote(
                    variables) + f'&doc_id={docid_dict["CometUFICommentsProviderPaginationQuery"]}'
                html = self._ha.getstring(url, postdata,
                                          headers="""
                accept: */*
                accept-encoding: gzip, deflate
                accept-language: en-US,en;q=0.9,zh;q=0.8
                content-length: {}
                content-type: application/x-www-form-urlencoded
                origin: https://www.facebook.com
                referer: {}
                sec-fetch-dest: empty
                sec-fetch-mode: cors
                sec-fetch-site: same-origin
                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36
                """.format(len(postdata), hostuser.url))
                resp_json = json.loads(html)
                resp_display_comments = resp_json['data']['feedback']['display_comments']
                before_count = resp_display_comments['before_count']
                has_previous_page = resp_display_comments['page_info']['has_previous_page']
                start_cursor = resp_display_comments['page_info']['start_cursor']
                start_cursor = '"' + start_cursor + '"'

                edges: list = resp_display_comments['edges']
                if len(edges) > 0:
                    for comment in self._parse_post_edges_v1(task, edges, post, hostuser):
                        yield comment
            # 向上展开评论, after输入end_cursor, first输入min(after_count, pagesize), last和before为null
            while has_next_page:
                # 每次请求间隔
                time.sleep(random.randint(0, 1))
                first = min(after_count, page_size)
                variables = '{' + f'"after":{end_cursor},"before":null,"displayCommentsFeedbackContext":null,"displayCommentsContextEnableComment":null,"displayCommentsContextIsAdPreview":null,"displayCommentsContextIsAggregatedShare":null,"displayCommentsContextIsStorySet":null,"feedLocation":"TIMELINE","feedbackID":"{postid_b64}","feedbackSource":0,"first":{first},"focusCommentID":null,"includeHighlightedComments":false,"includeNestedComments":true,"isInitialFetch":false,"isPaginating":true,"last":null,"scale":1,"topLevelViewOption":null,"useDefaultActor":false,"viewOption":null,"UFI2CommentsProvider_commentsKey":"ProfileCometTimelineRoute"' + '}'
                postdata = f'av={self._userid}&__user={self._userid}&__a=1&__csr=&__beoa=0&__pc={parse.quote(self._pc)}&dpr=1&__ccg=EXCELLENT&__hsi={self.hsi}&__comet_req=1&fb_dtsg={parse.quote(self.fb_dtsg)}&jazoest={self.jazoest}&__spin_r={self._spin_r}&__spin_b={self._spin_b}&__spin_t={self._spin_t}&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=CometUFICommentsProviderPaginationQuery&variables=' + parse.quote(
                    variables) + f'&doc_id={docid_dict["CometUFICommentsProviderPaginationQuery"]}'
                html = self._ha.getstring(url, postdata,
                                          headers="""
                accept: */*
                accept-encoding: gzip, deflate
                accept-language: en-US,en;q=0.9,zh;q=0.8
                content-length: {}
                content-type: application/x-www-form-urlencoded
                origin: https://www.facebook.com
                referer: {}
                sec-fetch-dest: empty
                sec-fetch-mode: cors
                sec-fetch-site: same-origin
                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36
                """.format(len(postdata), hostuser.url))
                resp_json = json.loads(html)
                resp_display_comments = resp_json['data']['feedback']['display_comments']
                after_count = resp_display_comments['after_count']
                has_next_page = resp_display_comments['page_info']['has_next_page']
                end_cursor = resp_display_comments['page_info']['end_cursor']
                end_cursor = '"' + end_cursor + '"'

                edges: list = resp_display_comments['edges']
                if len(edges) > 0:
                    for comment in self._parse_post_edges_v1(task, edges, post, hostuser):
                        yield comment
        except Exception:
            self._logger.error(
                "Get fb comments error:\nuserid={}\nusername={}\nerror:{}".format(
                    hostuser._userid, hostuser.nickname,
                    traceback.format_exc()))

    def _parse_post_edges_v1(self,
                             task: IscoutTask,
                             edges: list,
                             post: NetworkPost,
                             hostuser: NetworkProfile) -> iter:
        """每一条评论或者评论的评论就是一个edge, post是父评论"""
        try:
            for edge in edges:
                feedback = edge['node']['feedback']
                author_id = edge['node']['author']['id']
                author_name = edge['node']['author']['name']
                posttime = helper_time.timespan_to_datestr(edge['node']['created_time'])
                commentid = helper_str.base64_decode(feedback['id'])

                comment: NetworkPost = NetworkPost(commentid, self._SOURCE, author_id, isroot=False,
                                                   parentpostid=post.postid)
                comment.nickname = author_name
                comment.posttime = posttime
                comment.posturl = edge['node']['url']
                comment.likecount = feedback['reactors']['count']
                if comment.likecount > 0:
                    self._get_post_likes_v1(comment, hostuser)
                # preferred_body,body,body_renderer都有text, 区别？
                if not edge['node']['preferred_body'] is None:
                    comment.text = edge['node']['preferred_body']['text']
                # 附加的资源（图片，视频）
                attachments: list = edge['node']['attachments']
                if len(attachments) > 0:
                    for rsc in self._parse_post_attachments_v1(task, attachments, comment, hostuser):
                        if not rsc is None:
                            yield rsc

                if 'display_comments' in feedback:
                    comment.replycount = feedback['comment_count']['total_count']
                # 先返回该评论
                yield comment
                # 如果有,返回评论的评论
                if 'display_comments' in feedback:
                    display_reply_comments = feedback['display_comments']
                    for reply_comment in self._parse_post_display_comments_v1(task, display_reply_comments, comment, hostuser):
                        if not reply_comment is None:
                            yield reply_comment
        except Exception:
            self._logger.error(
                "Parse fb edges error:\nuserid={}\nusername={}\nerror:{}".format(
                    hostuser._userid, hostuser.nickname,
                    traceback.format_exc()))

    def _parse_post_attachments_v1(self,
                                   task: IscoutTask,
                                   attachments: list,
                                   post: NetworkPost,
                                   hostuser: NetworkProfile) -> iter:
        """处理推文或评论的图片、视频等附加资源"""
        try:
            retry_count = 0
            for attachment in attachments:
                if 'attachment' not in attachment['style_type_renderer']:
                    continue
                attachment = attachment['style_type_renderer']['attachment']
                if 'all_subattachments' in attachment:
                    nodes = attachment['all_subattachments']['nodes']
                else:
                    nodes = [attachment]
                for node in nodes:
                    media = node['media']
                    rsc = None
                    srcurl = ''
                    if media['__typename'] == 'Photo':
                        if 'image' in media:
                            srcurl = media['image']['uri']
                        else:
                            srcurl = media['photo_image']['uri']
                        rsc = NetworkResource(task, 'zplus', srcurl, 'facebook',
                                              EResourceType.Picture)
                    elif media['__typename'] == 'Video':
                        srcurl = media['playable_url']
                        rsc = NetworkResource(task, 'zplus', srcurl, 'facebook',
                                              EResourceType.Video)
                    elif media['__typename'] == 'Sticker':
                        if media.__contains__('sprite_image') and not media['sprite_image'] is None:
                            srcurl = media['sprite_image']['uri']
                        elif media.__contains__('sticker_image') and not media['sticker_image'] is None:
                            srcurl = media['sticker_image']['uri']
                        else:
                            srcurl = media['image']['uri']
                        rsc = NetworkResource(task, 'zplus', srcurl, 'facebook',
                                              EResourceType.Picture)
                    # 分享的链接，直接返回rsc，不下载
                    elif media['__typename'] == 'GenericAttachmentMedia':
                        if node.__contains__('story_attachment_link_renderer') and \
                                node['story_attachment_link_renderer'].__contains__('attachment') and \
                                node['story_attachment_link_renderer']['attachment'].__contains__('web_link'):
                            web_link = node['story_attachment_link_renderer']['attachment']['web_link']
                            srcurl = web_link['url']
                            rsc = NetworkResource(task, 'zplus', srcurl, 'facebook',
                                                  EResourceType.Url)
                            rsc.resourceid = web_link['fbclid']
                            post.set_resource(rsc)
                            yield rsc
                            continue
                    else:
                        self._logger.debug("Parse fb attachment debug: not processed type: {}".format(media['__typename']))
                        raise Exception

                    if not rsc is None and srcurl != '':
                        m = self._re_rsc_name.search(srcurl)
                        rscname = None
                        if not m is None:
                            rscname = m.group(1).strip()
                        if not rscname is None and rscname != '':
                            rsc.filename = rscname
                            rsc.resourceid = rscname
                            if rsc.filename.__contains__('.'):
                                rsc.extension = rsc.filename.split('.')[-1]
                        # 请求失败后会再次请求2次
                        while True:
                            try:
                                # 每次请求间隔
                                time.sleep(random.randint(1, 2))
                                rsc.stream = self._ha.get_response_stream(srcurl, timeout=60,
                                                                          headers='''
                                accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
                                accept-encoding: gzip, deflate
                                accept-language: en-US,en;q=0.9
                                cache-control: no-cache
                                pragma: no-cache
                                sec-fetch-dest: document
                                sec-fetch-mode: navigate
                                sec-fetch-site: none
                                sec-fetch-user: ?1
                                upgrade-insecure-requests: 1
                                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36
                                ''')
                                break
                            except:
                                # 请求超时，大概率是下载太频繁了
                                retry_count += 1
                                if retry_count > 2:
                                    return
                                self._logger.info(
                                    "Download fb attachment failed: retry {}".format(retry_count))
                                time.sleep(20)
                        post.set_resource(rsc)
                        yield rsc
        except Exception:
            self._logger.error(
                "Parse fb attachment error:\nuserid={}\nusername={}\nerror:{}".format(
                    hostuser._userid, hostuser.nickname,
                    traceback.format_exc()))

    def _get_post_likes_v1(self, post: NetworkPost,
                           hostuser: NetworkProfile):
        """
        拉取主推文点赞人员
        postid_b64是返回推文数据里feedback里面的id
        """
        try:
            postid_b64 = helper_str.base64str(post.postid)
            url = 'https://www.facebook.com/api/graphql/'
            docid_dict = self._get_docid_dict()
            if docid_dict == {} or docid_dict is None:
                self._logger.error("Get docid failed")
                return
            # 打开点赞人员列表
            time.sleep(random.randint(1, 2))
            variables = '{' + f'"feedbackTargetID":"{postid_b64}","reactionType":"NONE","scale":1' + '}'
            postdata = f'av={self._userid}&__user={self._userid}&__a=1&__csr=&__beoa=0&__pc={parse.quote(self._pc)}&dpr=1&__ccg=EXCELLENT&__hsi={self.hsi}&__comet_req=1&fb_dtsg={parse.quote(self.fb_dtsg)}&jazoest={self.jazoest}&__spin_r={self._spin_r}&__spin_b={self._spin_b}&__spin_t={self._spin_t}&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=CometUFIReactionsDialogQuery&variables=' + parse.quote(
                variables) + f'&doc_id={docid_dict["CometUFIReactionsDialogQuery"]}'
            html = self._ha.getstring(url, postdata,
                                      headers="""
            accept: */*
            accept-encoding: gzip, deflate
            accept-language: en-US,en;q=0.9,zh;q=0.8
            content-length: {}
            content-type: application/x-www-form-urlencoded
            origin: https://www.facebook.com
            referer: {}
            sec-fetch-dest: empty
            sec-fetch-mode: cors
            sec-fetch-site: same-origin
            user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36
            """.format(len(postdata), hostuser.url))
            resp = json.loads(html)
            jedges = resp['data']['node']['reactors']['edges']
            for reactor in jedges:
                nickname = reactor['node']['name']
                userid = reactor['node']['id']
                one = NetworkProfile(nickname, userid, "facebook")
                one.nickname = nickname
                post.set_likes(one)

            # 点赞列表翻页
            page_info = resp['data']['node']['reactors']['page_info']
            has_next_page = page_info['has_next_page']
            end_cursor = page_info['end_cursor']
            while has_next_page:
                # 每次请求间隔
                time.sleep(random.randint(1, 2))
                variables = '{' + f'"count":10,"cursor":"{end_cursor}","feedbackTargetID":"{postid_b64}","reactionType":"NONE","scale":1,"id":"{postid_b64}"' + '}'
                postdata = f'av={self._userid}&__user={self._userid}&__a=1&__csr=&__beoa=0&__pc={parse.quote(self._pc)}&dpr=1&__ccg=EXCELLENT&__hsi={self.hsi}&__comet_req=1&fb_dtsg={parse.quote(self.fb_dtsg)}&jazoest={self.jazoest}&__spin_r={self._spin_r}&__spin_b={self._spin_b}&__spin_t={self._spin_t}&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=CometUFIReactionsDialogTabContentRefetchQuery&variables=' + parse.quote(
                    variables) + f'&doc_id={docid_dict["CometUFIReactionsDialogTabContentRefetchQuery"]}'
                html = self._ha.getstring(url, postdata,
                                          headers="""
                accept: */*
                accept-encoding: gzip, deflate
                accept-language: en-US,en;q=0.9,zh;q=0.8
                content-length: {}
                content-type: application/x-www-form-urlencoded
                origin: https://www.facebook.com
                referer: {}
                sec-fetch-dest: empty
                sec-fetch-mode: cors
                sec-fetch-site: same-origin
                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36
                """.format(len(postdata), hostuser.url))
                resp = json.loads(html)
                if 'errors' in resp:
                    # 请求太频繁返回错误, 等待10s
                    if resp['errors'][0]['message'] == 'Rate limit exceeded':
                        self._logger.info('Get fb like failed: Rate limit exceeded. Retry')
                        time.sleep(10)
                        continue
                jedges = resp['data']['node']['reactors']['edges']
                for reactor in jedges:
                    nickname = reactor['node']['name']
                    userid = reactor['node']['id']
                    one = NetworkProfile(nickname, userid, "facebook")
                    one.nickname = nickname
                    post.set_likes(one)
                page_info = resp['data']['node']['reactors']['page_info']
                has_next_page = page_info['has_next_page']
                end_cursor = page_info['end_cursor']
        except Exception:
            self._logger.error('Got post likes fail: {}, {}'.format(post.postid, traceback.format_exc()))

