# -*- coding: utf-8 -*-
import json

import scrapy
from selenium.webdriver import ActionChains

from PocketLifeSpider.items import MovieItem
from PocketLifeSpider.util.MongoDbUtils import MongoDbUtils
from PocketLifeSpider.util.CommonUtils import *


class YoukuSpider(scrapy.Spider):
    name = 'youku'
    allowed_domains = ['list.youku.com']
    curr_year = '2019'
    start_urls = []
    domain = 'http://list.youku.com'

    # 数字与影视类型对应关系
    type_dic = {'96': '电影', '97': '电视剧', '85': '综艺', '100': '动漫', '177': '少儿'}
    # 数字与影视后缀对应关系
    type_suffix_dic = {'96': '片', '97': '剧', '85': '片', '100': '片', '177': '片'}

    # 电影总数
    pageSize = 84
    totalPage = 10
    total = pageSize * totalPage * len(start_urls)
    total_valid = 0
    index = 0
    target = None

    custom_settings = {
        'ITEM_PIPELINES': {
            'PocketLifeSpider.pipelines.ZuidaSpiderPipeline': 300,
        }
    }

    def __init__(self, target=None, name=None, **kwargs):
        super(YoukuSpider, self).__init__(name, **kwargs)
        self.target = target
        # 影视类型数字列表
        type_num_list = ['96', '97', '85', '100', '177']
        if (self.target == 'all'):
            for tmp_type_num in type_num_list:
                url = 'https://list.youku.com/category/show/c_'+tmp_type_num+'.html'
                html = get_one_page(url)
                html = etree.HTML(html)
                for a in html.xpath('//div[@class="yk-filter-panel"]/div[4]/ul/li/a'):
                    a_href = get_str_from_xpath(a.xpath('./@href'))
                    if ('r_' not in a_href):
                        continue
                    year = a_href.split('r_')[1].split('.html')[0]
                    url = 'https://list.youku.com/category/page?c='+tmp_type_num+'&r='+year+'&type=show&p=1'
                    self.start_urls.append(url)
        elif (self.target == 'latest'):
            for tmp_type_num in type_num_list:
                self.start_urls.append('https://list.youku.com/category/page?c=' + tmp_type_num + '&type=show&p=1')
            self.totalPage = 1
            self.total = self.totalPage * self.pageSize * len(self.start_urls)
        self.start_urls = reverse_arr(self.start_urls)

    def parse(self, response):

        # 开始时间
        start = time.time()
        driver = get_driver(0)

        # 获取所有电影的 id，用于判断电影是否已经爬取
        collection = 'movie'
        db_utils = MongoDbUtils(collection)
        dict = [{'sources': {'$elemMatch': {'$ne': []}}}, {'id': 1}]
        data = db_utils.find(dict)
        movie_ids = []
        for movie_id in data:
            movie_ids.append(movie_id['id'])

        # 获取影视类型
        origin_url = response.url
        # 影视类型对应数字
        type_num = origin_url.split('c=')[1].split('&')[0]
        # 影视类型
        movie_type = self.type_dic.get(type_num)
        # 影视后缀
        type_suffix = self.type_suffix_dic.get(type_num)


        # 生成视频列表地址
        for i in reverse_arr(range(1, self.totalPage + 1)):
            url = origin_url.split('p=')[0] + 'p=' + str(i)
            print(url)
            response = get_response(url)
            if (len(response.json()['data']) == 0):
                self.index = self.index + self.pageSize
            # 解析视频列表
            for list in reverse_arr(response.json()['data']):
                self.index = self.index + 1
                videoLink = 'https://v.youku.com/v_show/id_' + list['videoId'] + '.html'
                print(videoLink)
                movie_item = MovieItem()
                if (list['summary'] == '资料'):
                    print('跳过 -> ' + videoLink)
                    continue
                movie_item['src'] = list['img']
                movie_item['name'] = list['title']
                update_status = list['summary']
                if (update_status == None or update_status == ''):
                    update_status == '优酷视频'
                movie_item['update_status'] = update_status
                # 解析视频详情
                movie_item['id'] = videoLink.split('.html')[0].split('show/')[1]
                try:
                    driver.get(videoLink)
                except:
                    print('跳过 -> ' + videoLink)
                    continue
                initial_data = driver.execute_script('return window.__INITIAL_DATA__')
                if (initial_data is None):
                    print('跳过 -> ' + videoLink)
                    continue
                movie_item['nickname'] = (str)(initial_data['data']['data']['data']['extra']['showSubtitle'])
                release_date = (str)(initial_data['data']['data']['nodes'][0]['nodes'][0]['nodes'][0]['data']['showReleaseYear'])
                movie_item['release_date'] = reverse_release_date(release_date)
                try:
                    score = (str)(initial_data['data']['data']['nodes'][0]['nodes'][0]['nodes'][0]['data']['youkuRate'])
                except:
                    score = get_random_str()
                movie_item['score'] = score
                actors = []
                for node in initial_data['data']['data']['nodes'][0]['nodes'][0]['nodes']:
                    if ('subtitle' in node['data'] and '饰' in node['data']['subtitle']):
                        actors.append((str)(node['data']['title']))
                movie_item['actors'] = actors
                directors = []
                for node in initial_data['data']['data']['nodes'][0]['nodes'][0]['nodes']:
                    if ('subtitle' in node['data'] and node['data']['subtitle'] == '导演'):
                        directors.append((str)(node['data']['title']))
                movie_item['directors'] = directors
                region = (str)(initial_data['data']['data']['nodes'][0]['nodes'][0]['nodes'][0]['data']['area'][0])
                movie_item['region'] = reverse_region(region)
                movie_item['type'] = movie_type
                try:
                    type2 = (str)(initial_data['data']['data']['nodes'][0]['nodes'][0]['nodes'][0]['data']['showGenre'].split(' ')[0])
                except:
                    type2 = '其他'
                if (type_num == '177'): type2 = '少儿片'
                if (type_num != '85'):
                    if (type2 == ''):
                        type2 = '其他'
                    elif (type2.endswith(type_suffix) == False):
                        type2 = type2 + type_suffix
                if (is_exclude_type2(type2) == True):
                    continue
                movie_item['type2'] = reverse_type2(type2)
                movie_item['description'] = (str)(initial_data['data']['data']['nodes'][0]['nodes'][0]['nodes'][0]['data']['desc'])
                movie_item['update_time'] = (str)(initial_data['data']['data']['data']['extra']['showReleaseTime'])
                movie_item['language'] = '内详'
                movie_item['duration'] = '0'
                if (movie_item['name'] == '乡村爱情12'):
                    print('')
                # 解析播放列表
                driver.get(videoLink)
                page_config = driver.execute_script('return window.PageConfig')
                if (page_config is None):
                    print('跳过 -> ' + videoLink)
                    continue
                showid = page_config['showid']
                sources = []
                source = {'name': '优酷视频', 'types': []}
                types = []
                for page in range(1, 60):
                    url = 'https://v.youku.com/page/playlist?&showid=' + showid + '&videoCategoryId=' + type_num + '&isSimple=false&videoEncodeId=' + \
                          movie_item['id'].split('id_')[1] + '%3D%3D&page=' + (str)(page)
                    print(url)
                    html = get_one_page(url)
                    html = json.loads(html)['html']
                    html = etree.HTML(html)
                    # 如果页数已经超过有效页数，则停止获取下面的页数的资源类型
                    if (html == None):
                        break
                    for each in html.xpath('//div[@class="item item-cover" or @class="item item-num" or @class="item item-num item-num-last" or @class="item item-txt"]'):
                        type = {'name': '', 'url': ''}
                        type_name = reverse_type_name(get_str_from_xpath(each.xpath('./@seq')))
                        url = 'https:' + get_str_from_xpath(each.xpath('./a/@href'))
                        type['name'] = type_name
                        type['url'] = url
                        print('正在爬取 ' + movie_type + ' ' + (str)(i) + '/' + (str)(self.totalPage) + ' ' + (str)(
                            self.index) + '/' + (str)(self.total) + ' -> ' + movie_item['id'] + ' ' + source[
                                  'name'] + ' ' + type['name'])
                        types.append(type)
                source['types'] = types
                sources.append(source)
                # 跳过播放列表为空的视频并记录
                if (len(types) == 0):
                    continue
                movie_item['sources'] = sources
                # 视频已爬取且未更新
                if (is_need_source(movie_item, 'movie') == False):
                    print(movie_item['id'] + ' 已爬取')
                    continue
                yield movie_item
                self.total_valid = self.total_valid + 1
        # 结束时间
        driver.quit()
        end = time.time()
        process_time = end - start
        print('本次共爬取 ' + str(self.total_valid) + ' 条数据，用时 ' + str(process_time) + 's')