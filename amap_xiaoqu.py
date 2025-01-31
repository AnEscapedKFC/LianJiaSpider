import pandas as pd
import requests
import time
import chardet
import re


def keep_first_parentheses_content(s: str) -> str:
    """
    如果字符串中存在两个或以上的中文括号对（“（”和“）”），
    则只保留第一个括号内的内容，否则返回原字符串。
    """
    # 这个正则会匹配“（”与“）”之间的文本，并仅捕获其中的内容
    pattern = r'（([^）]*)）'
    matches = re.findall(pattern, s)

    # 如果匹配到两组或以上的括号内容，则返回第一组的内容
    if len(matches) >= 2:
        return matches[0]
    else:
        # 否则直接返回原字符串
        return s


# 1. 读取原始CSV文件


def get_geocode(address, api_key, base_url, max_retries=3, base_sleep=0.5):
    """
    获取地址的经纬度，并在获取失败时重试 max_retries 次。

    :param address: 要查询的地址（小区名称）
    :param api_key: 高德地图API Key
    :param base_url: 高德地图地理编码服务接口地址
    :param max_retries: 最大重试次数
    :param base_sleep: 每次重试之间的等待时长（秒）
    :return: (lng, lat) 或 (None, None)
    """
    address = keep_first_parentheses_content(address)
    for attempt in range(1, max_retries + 1):
        try:
            params = {
                "key": api_key,
                "address": f"上海市{address}",  # 拼接完整地址
            }
            response = requests.get(base_url, params=params, timeout=10)
            # 判断HTTP状态码
            if response.status_code == 200:
                data = response.json()
                # 判断高德返回结果
                if data.get("status") == "1" and data.get("count") != "0":
                    location = data["geocodes"][0]["location"]
                    lng, lat = location.split(',')
                    return lng, lat
                else:
                    print(
                        f"[第 {attempt} 次请求] 无法获取到经纬度，status={data.get('status')}, count={data.get('count')}")
            else:
                print(f"[第 {attempt} 次请求] HTTP请求失败，状态码：{response.status_code}")
        except Exception as e:
            print(f"[第 {attempt} 次请求] 调用高德地图出现异常：{e}")

        # 若未成功获取或出现异常，则等待再重试
        if attempt < max_retries:
            print(f"等待 {base_sleep} 秒后进行第 {attempt + 1} 次重试...\n")
            time.sleep(base_sleep)

    # 如果重试多次仍失败，返回空值
    return None, None


if __name__ == "__main__":
    # 这里可以具体到门牌号，因此不需要区名
    input_file = input("请输入小区表格文件路径(*.csv)：").strip()  # 修改为实际文件名
    output_file = input("请输入输出文件路径(*.csv)：").strip()
    with open(input_file, 'rb') as f:
        result = chardet.detect(f.read())  # 读取一定量的数据进行编码检测

    print("检测到的文件编码：", result['encoding'])

    # 根据检测的编码进行读取，如果失败则使用 utf-8
    try:
        df = pd.read_csv(input_file, encoding=result['encoding'] or 'utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(input_file, encoding='utf-8')

    # 去除小区名称为空的数据
    df = df.dropna(subset=['小区名称'])
    df['经度'] = None
    df['纬度'] = None

    api_key = ""  # 替换为真实密钥
    base_url = "https://restapi.amap.com/v3/geocode/geo"
    max_retries = 3  # 最多重试次数

    for idx, row in df.iterrows():
        lng, lat = get_geocode(row['具体地址'], api_key, base_url, max_retries=max_retries, base_sleep=0.5)
        df.at[idx, '经度'] = lng
        df.at[idx, '纬度'] = lat

        # 控制请求频率（每条记录之后再休眠0.2秒, 可根据需要调整）
        time.sleep(0.2)

    # 6. 保存结果到CSV
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"处理完成，结果已保存至：{output_file}")
