import pandas as pd  # 数据存储
import requests  # 网页内容获取
import re  # 解析数据
from lxml import etree  # 解析数据
import random
import time  # 反反爬
from fastprogress import master_bar, progress_bar  # 进度条显示


def ua():
    """随机获取一个浏览器用户信息"""
    agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0'
    # 如果触发人机验证了，换一个浏览器cookie
    cookie = ''
    return {
        'User-Agent': agent,
        'Cookie': cookie
    }


def get(url):
    """
    获取网页源码
    url: 目标网页的地址
    return:网页源码
    """
    res = requests.get(url=url, headers=ua())
    return res.text


def get_url(res_text):
    """
    获取源码中每个二手房详情页的url
    res_text:网页源码
    return:列表形式的30个二手房详情页的url
    """
    re_f = '<a class="" href="(.*?)" target="_blank"'
    url_list = re.findall(re_f, res_text)
    return url_list


def get_else_data(res_text):
    res_text = etree.HTML(res_text)

    title = res_text.xpath("//div[@class='sellDetailHeader']//h1/@title")

    return dict(zip(['标题'], [title]))


def safe_get(lst, idx, default=""):
    """
    安全获取列表的元素:
      - 若索引 idx 合法，则返回 lst[idx]
      - 若索引越界，则返回 default
    """
    return lst[idx] if 0 <= idx < len(lst) else default


def get_data(res_text):
    """获取房屋的详细数据"""

    # 将字符串解析为 HTML Element 对象
    html = etree.HTML(res_text)

    #------------------#
    # 1. 获取主要字段  #
    #------------------#
    # 标题
    title_list = html.xpath("//div[@class='sellDetailHeader']//h1/@title")
    title = safe_get(title_list, 0)

    # 总价、单价（注意：这里用到了下标2,3，所以需先把结果放到列表中）
    price_list = html.xpath("//div[@class='overview']//div/span/text()")
    total_price = safe_get(price_list, 2)  # 若下标不存在则返回""
    unit_price = safe_get(price_list, 3)

    # 地段（可能会有多项，这里直接保留原列表）
    place = html.xpath("//div[@class='overview']//div/span/a/text()")

    # 小区名称
    location_list = html.xpath("//div[@class='overview']//div/a/text()")
    # 安全获取可能的下标
    location = safe_get(location_list, 1)
    if location == "地图":
        location = safe_get(location_list, 0)

    #--------------------#
    # 2. 获取房屋基本信息 #
    #--------------------#
    # 基本信息的“标题部分”（lab）
    lab = html.xpath("//div[@class='base']//span/text()")
    # 基本信息的“内容部分”（val）
    val_raw = html.xpath("//div[@class='base']//li/text()")
    val = [item.strip() for item in val_raw if item.strip()]

    #--------------------#
    # 3. 获取房源交易信息 #
    #--------------------#
    key1 = html.xpath("//div[@class='transaction']//span[1]//text()")
    trans_raw = html.xpath("//div[@class='transaction']//span[2]//text()")
    trans = [item.strip() for item in trans_raw if item.strip()]

    #--------------------#
    # 4. 获取房源特色信息 #
    #--------------------#
    # 特色标题
    key = html.xpath("//div[@class='baseattribute clear']/div[@class='name']/text()")
    # 特色内容
    val1_raw = html.xpath("//div[@class='baseattribute clear']/div[@class='content']/text()")
    val1 = [item.strip() for item in val1_raw if item.strip()]

    #---------------------------------#
    # 5. 将所有数据整合为一个字典返回  #
    #---------------------------------#
    # 先把固定的几个主键、主值放进列表
    dict_keys = ['标题', '总价格', '单价', '地段', '小区名称']
    dict_vals = [title, total_price, unit_price, place, location]

    # 然后把 lab + key1 + key 扩展到键列表里
    dict_keys.extend(lab)
    dict_keys.extend(key1)
    dict_keys.extend(key)

    # 把 val + trans + val1 扩展到值列表里
    dict_vals.extend(val)
    dict_vals.extend(trans)
    dict_vals.extend(val1)

    # 使用 zip 构建键值对；长度不等时，以较短的为准
    # （如果想要完全保留多余项，可以根据需要自行处理）
    min_len = min(len(dict_keys), len(dict_vals))
    result = dict(zip(dict_keys[:min_len], dict_vals[:min_len]))

    return result

def main(qu, start_pg=1, end_pg=100, download_times=1):
    """爬虫程序
    qu: 传入要爬取的qu的拼音的列表
    start_pg:开始的页码
    end_pg:结束的页码
    download_times:第几次下载
    """
    for q in qu:
        # 获取当前区的首页url
        url = 'https://sh.lianjia.com/ershoufang/' + q + '/'
        # 数据储存的列表
        data = []
        # 文件保存路径
        filename = '二手房-' + q + '第' + str(download_times) + '次下载.csv'

        print('二手房-' + q + '第' + str(download_times) + '次下载')
        mb = master_bar(range(start_pg, end_pg + 1))

        for i in mb:

            # 获取每页的url
            new_url = url + 'pg' + str(i) + '/'

            # 获取当前页面包含的30个房屋详情页的url
            url_list = get_url(get(new_url))

            for l in progress_bar(range(len(url_list)), parent=mb):
                print('正在爬取第' + str(i + 1) + '页数据!!')
                # 反爬随机停止一段时间
                a = random.randint(2, 5)
                if l % a == 0:
                    time.sleep(0.02 * random.random())

                # 获取当前页面的源码
                text = get(url_list[l])
                # 获取当前页面的房屋信息
                data.append(get_data(text))
                # 反爬随机停止一段时间
                time.sleep(1 * random.random())
                mb.child.comment = '正在爬取第' + str(l + 1) + '条数据!!'
            mb.main_bar.comment = '正在爬取第' + str(i + 1) + '页数据!!'

            # 反爬随机停止一段时间
            time.sleep(0.05 * random.random())

            if i % 5 == 0:
                # 每5页保存一次数据
                pd.DataFrame(data).to_csv(filename, encoding='utf-8')
                mb.write('前' + str(i) + '页数据已保存')


Qu = []
qu_name = input("请输入区（拼音）：").strip()
Qu.append(qu_name)
main(Qu)
