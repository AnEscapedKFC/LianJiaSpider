import pandas as pd  # 数据存储
import requests  # 网页内容获取
import re  # 解析数据
from lxml import etree  # 解析数据
import random
import time  # 反反爬
from fastprogress import master_bar, progress_bar  # 进度条显示


def ua():
    """随机获取一个浏览器用户信息"""
    # 现在访问链家需要带上cookie，不然会触发登录验证
    # 随机浏览器头似乎没有必要，现在只用一个也不会频繁触发反爬
    # 如果触发反爬，就换另一个浏览器的cookie
    agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0'
    # cookie = 'lianjia_uuid=94d1b14e-97b6-4e3a-b5c0-6eb5232f51f7; crosSdkDT2019DeviceId=ijewj3-vtswrp-yni6vnelb1051za-kedqog7bp; lfrc_=51726a02-16b8-47aa-829f-cb383278da46; _ga=GA1.2.564544161.1737984287; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22194a7ef7603929-00101cafdc84cf-26011b51-1338645-194a7ef76041201%22%2C%22%24device_id%22%3A%22194a7ef7603929-00101cafdc84cf-26011b51-1338645-194a7ef76041201%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_referrer%22%3A%22%22%2C%22%24latest_referrer_host%22%3A%22%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%7D%7D; _jzqx=1.1737984276.1738037504.4.jzqsr=hip%2Elianjia%2Ecom|jzqct=/.jzqsr=sh%2Elianjia%2Ecom|jzqct=/; select_city=310000; _jzqckmp=1; _gid=GA1.2.2132759657.1738211647; login_ucid=2000000463884432; lianjia_token=2.0010f9fa8e46dcc7f20154d3bfd42f4b28; lianjia_token_secure=2.0010f9fa8e46dcc7f20154d3bfd42f4b28; security_ticket=Gnu+58JlcuU7OJKTODobW9iQbx0rUtefi83LN3CayW7XtuUZcdh3WbbPyvxKupUYR5BOlAXP1u/dInsGDz4fSPIXB3STwM8kF4KjpGF6d6K14lYcUf+d9lE8B3ODG9Ro7Is70/VGTNC9ihaZGWJUF9HsGc3xv5ZEL+ol14sSP3A=; ftkrc_=62785f10-9ce1-4df3-bf31-b142a6b55fc0; hip=ORXbFygHI2OxNmt_aZnH3Y_sVdkCdxBn8nVkutkKaIEVR4gahYy14O-gvqmaS-WsW_pgSVXs48JRfWGBuqqxLSPY_l1LcedCBY-E3SSz-gdNwgslxVqXKZW2Png7Xepl39yz7rsXvvvBxj_VWPJWoMfwXLjp_kk_y5TEdit2Rdid7KiaR-HbL8vLmQ%3D%3D; lianjia_ssid=4c4c4122-466b-4784-8e4e-bfe925a76861; _qzjc=1; _jzqa=1.621711060713241100.1737984276.1738231218.1738234234.11; _jzqc=1; Hm_lvt_46bf127ac9b856df503ec2dbf942b67e=1737986814,1738027025,1738211636,1738234234; HMACCOUNT=56B08FE60175ECE3; _ga_LRLL77SF11=GS1.2.1738234260.11.1.1738235016.0.0.0; _ga_GVYN2J1PCG=GS1.2.1738234260.11.1.1738235016.0.0.0; Hm_lpvt_46bf127ac9b856df503ec2dbf942b67e=1738235742; _qzja=1.1966590649.1737984275841.1738231217690.1738234234086.1738235738846.1738235742433.0.0.0.76.11; _qzjb=1.1738234234085.10.0.0.0; _qzjto=31.4.0; _jzqb=1.10.10.1738234234.1; srcid=eyJ0Ijoie1wiZGF0YVwiOlwiZjI0ZGQ4Yjk3NWFmMzkzN2VlMDA0OTQzMjQ1ZWJiY2YyMDkwODRlMmMzOGFmYjU5ZTY3NjU2OGU0NzdiNGNkZWFjOWIyN2Q2NDA0MWQ1NzQ3NGYxZGU0NmMxOWQwYjcxOGI3ODI5MDg3ODU4NmIyMGZlMGM5OGZhMmYzZmZjYmQ1YjY5MGZjYmM5MGYyYjQ1MjA5Y2M4Yjg1OWZmMWU3ZjNhMWE5MzkyZDJmMTEyZDk2OTdjNzA3MTc4Mjk5OTY0NmVkOWQ2M2VmODMxMWYxMmU2YjhjYzMzNjQ3NWQyNzM4MTI3YzQ0YzU0YTI3ZTM0ODUyMTg0ZjhlOTAxMDcxM1wiLFwia2V5X2lkXCI6XCIxXCIsXCJzaWduXCI6XCJiNTNlNTQ4OVwifSIsInIiOiJodHRwczovL3NoLmxpYW5qaWEuY29tL3hpYW9xdS9taW5oYW5nL3BnMS8iLCJvcyI6IndlYiIsInYiOiIwLjEifQ=='
    cookie = ''
    return {
        'User-Agent': agent,
        'Cookie': cookie
    }


def validate_urls(url_list):
    """
    验证列表中的URL是否符合指定格式。

    参数:
    url_list (list): 包含URL的列表

    返回:
    list: 符合格式的URL列表
    """
    # 编译正则表达式
    pattern = re.compile(r'^https://sh\.lianjia\.com/xiaoqu/\d{13}/$')

    # 使用列表推导式过滤符合条件的URL
    valid_urls = [url for url in url_list if pattern.match(url)]

    return valid_urls


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
    return:列表形式的30个小区详情页的url
    """
    re_f = '<a href="(.*?)" target="_blank"'  # 例：<a href="https://sh.lianjia.com/xiaoqu/5011000005141/" target="_blank"
    # 注意，如果采用这种写法会匹配到一些错误的url，因此，需要对得到的列表内容进行二次正则表达式验证
    url_list = re.findall(re_f, res_text)
    return validate_urls(url_list)


def get_data(res_text):
    """获取房屋的详细数据"""

    # 将字符串解析为 HTML Element 对象
    html = etree.HTML(res_text)

    # 获取主要字段  #
    xiaoqu_header = html.xpath("//div[@class='xiaoquDetailHeader']")
    xiaoqu_header_elem = xiaoqu_header[0]
    # 用 .// 表示“在当前节点下查找所有子孙”。
    detail_title = xiaoqu_header_elem.xpath(".//h1[@class='detailTitle']/text()")[0]  # 小区名称
    if detail_title == "暂无信息":
        return None
    detail_desc = xiaoqu_header_elem.xpath(".//div[@class='detailDesc']/text()")[0]  # 具体门牌号（用于地理编码）
    if detail_desc == "暂无信息":
        return None
    detail_desc = detail_desc.split(',')[0]
    detail_desc = detail_desc.split('，')[0]
    print(detail_desc)
    info_list = html.xpath("//div[@class='xiaoquOverview']//span[@class='xiaoquInfoContent']/text()")  # 这里会得到多个数据，使用正则表达式只保留建成时间
    build_time = info_list[6]  # 建成时间
    if(build_time[0]=='1'):  # 这里只看2000年后的房子
        return None
    if build_time == "暂无信息":
        return None
    avg_price_list = html.xpath("//div[@class='xiaoquOverview']//span[@class='xiaoquUnitPrice']/text()")
    if len(avg_price_list) == 0:
        avg_price = "000000"  # 这里可以直接返回None，具体看自己需求
    else:
        avg_price = avg_price_list[0]
    # # 将所有数据整合为一个字典返回  #
    # # 先把固定的几个主键、主值放进列表
    dict_keys = ['小区名称', '具体地址', '建成时间', '挂牌均价']
    dict_vals = [detail_title, detail_desc, build_time, avg_price]
    # # 使用 zip 构建键值对；长度不等时，以较短的为准
    # # （如果想要完全保留多余项，可以根据需要自行处理）
    min_len = min(len(dict_keys), len(dict_vals))
    result = dict(zip(dict_keys[:min_len], dict_vals[:min_len]))
    return result


def main(qu, start_pg=1, end_pg=30, download_times=1):  # 小区数据没这么多
    """爬虫程序
    qu: 传入要爬取的qu的拼音的列表
    start_pg:开始的页码
    end_pg:结束的页码
    download_times:第几次下载
    """
    for q in qu:
        # 获取当前区的首页url
        url = 'https://sh.lianjia.com/xiaoqu/' + q + '/'
        # 数据储存的列表
        data = []
        # 文件保存路径
        filename = '小区-' + q + '第' + str(download_times) + '次下载.csv'

        print('小区-' + q + '第' + str(download_times) + '次下载')
        mb = master_bar(range(start_pg, end_pg + 1))

        for i in mb:

            # 获取每页的url
            new_url = url + 'pg' + str(i) + '/'

            # 获取当前页面包含的30个房屋详情页的url
            url_list = get_url(get(new_url))

            for l in progress_bar(range(len(url_list)), parent=mb):
                # 反爬随机停止一段时间
                a = random.randint(2, 5)
                if l % a == 0:
                    time.sleep(0.02 * random.random())

                # 获取当前页面的源码
                text = get(url_list[l])
                info = get_data(text)
                if info == None:
                    continue
                # 获取当前页面的房屋信息
                data.append(info)
                # 反爬随机停止一段时间
                time.sleep(1 * random.random())
                mb.child.comment = '正在爬取第' + str(l + 1) + '条数据!!'
            mb.main_bar.comment = '正在爬取第' + str(i + 1) + '页数据!!'
            print('正在爬取第' + str(i) + '页数据!!')

            # 反爬随机停止一段时间
            time.sleep(0.05 * random.random())

            pd.DataFrame(data).to_csv(filename, encoding='utf-8')
            mb.write('前' + str(i) + '页数据已保存')

Qu = []
qu_name = input("请输入区（拼音）：").strip()
Qu.append(qu_name)
main(Qu)
