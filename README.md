 # 项目说明
本项目用于爬取链家网的二手房与小区板块的数据，并支持调用高德API计算出小区的经纬度，进而计算到目的地点的通勤距离与时间。脚本默认为上海地区，可根据自己需求修改url来更换城市。

## 脚本介绍
- **lianjia_ershoufang.py**: 爬取指定区的二手房数据并导出csv文件，最多一次性爬取100页。可根据自己的需求修改匹配字段。
- **lianjia_xiaoqu.py**: 爬取指定区的小区数据并导出csv文件。注意：小区板块中包含很多未挂牌无在售的小区，脚本默认过滤这些小区，可根据自己需求筛选。
> 小区板块中包含很多未挂牌无在售的小区，脚本默认过滤这些小区，可根据自己需求筛选
- **amap_ershoufang.py**: 根据`lianjia_ershoufang.py`导出的csv表格，统计所有小区的名称，在售房源数量以及均价。并根据小区名称调用高德API计算出小区经纬度并导出csv文件。结果可能会产生误差，造成计算的通勤距离与时间不准确。
- **amap_xiaoqu.py**: 根据`lianjia_xiaoqu.py`导出的csv表格，通过具体门牌号调用高德API计算经纬度并导出csv文件，精度更高。
- **Distance.py**: 两个amap脚本导出的csv表格中均包含了“小区名称”“经度”“纬度”列。该脚本接收输入的目的地址，转为经纬度后，通过遍历每个小区的经纬度计算出通勤距离与时间，并导出csv表格。

> 注意: 默认地区为上海，若为其他地区，请修改`city`参数的值；当前采用的策略是躲避拥堵&不走高速，如果有其他需求，请修改`strategy`参数的值（具体见[高德地图API指南](https://lbs.amap.com/api/webservice/guide/api/direction/)）。

## 爬虫原理

链家的反爬力度并不大，请求带上cookie后一般就不会触发登录与反爬验证。如果触发了就换个浏览器的cookie。

链家网的每个pg下会包含三十个详情页url，可以通过正则表达式从页面源码中取得：

    re_f = '<a href="(.*?)" target="_blank"' # 例：<a href="https://sh.lianjia.com/xiaoqu/5011000005141/" target="_blank"  
>注意，如果采用这种写法会匹配到一些错误的url，因此，需要对得到的列表内容进行二次正则表达式验证 （详情页url最后是13位数字，同样使用正则表达式进行筛选）

    pattern = re.compile(r'^https://sh\.lianjia\.com/xiaoqu/\d{13}/$')

得到详情页url列表后，访问每个详情页得到页面源码，这里采用xpath，首先将原始html转化为一个可以用 XPath 查询的 HTML DOM 对象。

      html = etree.HTML(res_text)

之后使用 XPath 语法从 DOM 中找到指定的元素，例如

    detail_desc = xiaoqu_header_elem.xpath(".//div[@class='detailDesc']/text()")[0]  # 具体门牌号（用于地理编码）

这条语句的意思是在整个文档中查找所有`class="xiaoquDetailHeader"` 的 `<div>` 元素，返回一个列表。第一个元素就是小区的具体门牌号。可根据自己需要，结合页面源码区匹配所需字段。
>有的小区某些字段可能缺失，导致返回列表为空，要对此类情况做好处理。

获得全部字段后，返回一个键值对，保存为csv文件即可。

## 高德API调用
###  地理编码
构造请求：

    params = {  
        "key": api_key,  
        "address": f"上海市{address}",  # 拼接完整地址  
    }  
    response = requests.get(base_url, params=params, timeout=10)

address为必选参数，如果有具体门牌号的号建议优先使用门牌号，实测要比直接使用小区名称精度高很多。

可选参数有很多，具体见[地理/逆地理编码-基础 API 文档-开发指南-Web服务 API | 高德地图API](https://lbs.amap.com/api/webservice/guide/api/georegeo)
>需要注意，高德API会限制每秒访问次数，建议每次请求后等待一定时间，并且设置一个最大重试次数，若收到的响应不正确则重复请求，避免因为频率过高造成数据丢失。


### 路径规划
构造请求：

    url = "https://restapi.amap.com/v3/direction/driving"  
    params = {  
        "key": key,  
        "origin": f"{origin_lng},{origin_lat}",  
        "destination": f"{dest_lng},{dest_lat}",  
        "strategy": "15",        # 多条结果，躲避拥堵、路程较短、尽量缩短时间  
      "extensions": "base" # 只要基本信息，如需更详细可用 "all"闵行小区坐标.csv  
    }

strategy是一个重要的参数，表示驾车选择策略。具体使用见[路径规划-基础 API 文档-开发指南-Web服务 API | 高德地图API](https://lbs.amap.com/api/webservice/guide/api/direction)
这里的15会返回多条路径，但不知道为啥结果一样。不过结果与手机APP相差不大。

响应包含多个字段，其中包括了详细的路径规划数据，这里只保留了距离与时间，可结合官方文档根据自己的需求筛选字段。

    data = response.json()
    route = data.get("route", {})  
    paths = route.get("paths", [])
    for path in paths:  
        dist_str = path.get("distance", "0")  
        dur_str  = path.get("duration", "0")


