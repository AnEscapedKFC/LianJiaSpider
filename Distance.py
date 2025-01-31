import pandas as pd
import requests
import time

# 高德API key
GAODE_KEY = ""

# 最大重试次数
MAX_RETRIES = 3

# 每次请求后等待时间（秒）
REQUEST_INTERVAL = 0.2


def get_location_from_address(address, key=GAODE_KEY, max_retries=MAX_RETRIES):
    """
    通过高德地理编码API，根据地址获取经纬度。
    设置重试机制，如若失败则重试，最大重试次数为 max_retries。
    返回 (longitude, latitude)
    """
    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        "key": key,
        "address": address,
        "city": "shanghai"
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            # 每次请求后都等待 0.2s，避免过多请求导致被限
            time.sleep(REQUEST_INTERVAL)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "1" and data.get("geocodes"):
                    location_str = data["geocodes"][0]["location"]  # 格式： "lng,lat"
                    lng, lat = location_str.split(",")
                    return float(lng), float(lat)
                else:
                    print(f"[警告] 地理编码API返回异常信息: {data}")
            else:
                print(f"[警告] 地理编码API HTTP错误: {response.status_code}")
        except Exception as e:
            print(f"[错误] 第 {attempt + 1} 次请求地理编码API失败，异常信息: {e}")

        # 若本次请求失败，进入下一次重试
        print(f"[重试] 正在重试第 {attempt + 2} 次请求...")

    # 如果到达此处，说明多次请求仍失败
    raise Exception(f"地理编码API请求失败，超过最大重试次数 {max_retries}")


def get_two_fastest_routes(
    origin_lng, origin_lat,
    dest_lng, dest_lat,
    key=GAODE_KEY,
    max_retries=MAX_RETRIES
):
    """
    调用高德V3驾车路线规划接口 (strategy=10)，
    返回多条可行路线后，选出:
        1) 耗时最短(首选)
        2) 第二短(备选)
    并返回这两条路线的距离和耗时。

    返回:
        {
            "primary":  {"distance": int, "duration": int},
            "secondary":{"distance": int, "duration": int}
        }
      - 若只有1条路线，secondary 返回 None
      - 若无可行路线，则返回 None
    """
    url = "https://restapi.amap.com/v3/direction/driving"
    params = {
        "key": key,
        "origin": f"{origin_lng},{origin_lat}",
        "destination": f"{dest_lng},{dest_lat}",
        "strategy": "15",        # 多条结果，躲避拥堵、路程较短、尽量缩短时间
        "extensions": "base"     # 只要基本信息，如需更详细可用 "all"闵行小区坐标.csv
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            # 避免请求过快导致QPS限制
            time.sleep(REQUEST_INTERVAL)

            if response.status_code == 200:
                data = response.json()
                # status=1 表示请求成功
                if data.get("status") == "1":
                    route = data.get("route", {})
                    paths = route.get("paths", [])
                    if not paths:
                        print("[警告] 无可行路径，paths为空。")
                        return None

                    # 将paths按duration从小到大排序
                    parsed_paths = []
                    for path in paths:
                        dist_str = path.get("distance", "0")
                        dur_str  = path.get("duration", "0")
                        try:
                            dist_val = int(dist_str)
                            dur_val  = int(dur_str)
                        except ValueError:
                            dist_val = 0
                            dur_val  = 999999999

                        parsed_paths.append({
                            "distance": dist_val,
                            "duration": dur_val
                        })

                    # 按 “duration” 升序排序
                    parsed_paths.sort(key=lambda x: x["duration"])

                    # 取前两条
                    primary   = parsed_paths[0]
                    secondary = parsed_paths[1] if len(parsed_paths) > 1 else None

                    return {
                        "primary": primary,
                        "secondary": secondary
                    }
                else:
                    print(f"[警告] 请求成功但返回status!=1: {data}")
            else:
                print(f"[警告] HTTP状态码异常: {response.status_code}")
        except Exception as e:
            print(f"[错误] 第 {attempt+1} 次请求出现异常: {e}")

        print(f"[重试] 正在进行第 {attempt+2} 次尝试...")

    # 若到此仍未成功
    raise Exception(f"多次重试后仍无法获取路线规划结果。({max_retries} 次)")


def main():
    input_csv_path = input("请输入小区经纬表格文件路径(*.csv)：").strip()  # 替换为实际CSV路径
    df = pd.read_csv(input_csv_path, encoding="utf-8")  # 根据实际文件编码设置
    output_csv_path = input("请输入输出文件名称(*.csv)：").strip()  # 替换为实际CSV路径
    # 输入目标地址，通过高德地图获取坐标
    target_address = input("请输入目标地址：").strip()
    try:
        target_lng, target_lat = get_location_from_address(target_address)
        print(f"目标地址 '{target_address}' 的坐标是：lng={target_lng}, lat={target_lat}")
    except Exception as e:
        print(f"[错误] 无法获取目标地址的经纬度: {e}")
        return
    time.sleep(1)
    # 为结果新增两列：驾车距离(米)、所需时间(秒)
    distances = []
    durations = []
    sec_distances = []
    sec_durations = []
    for idx, row in df.iterrows():
        origin_lng = row["经度"]
        origin_lat = row["纬度"]

        try:
            result = get_two_fastest_routes(
                origin_lng, origin_lat,
                target_lng, target_lat
            )
            primary = result["primary"]  # 一定不为空
            secondary = result["secondary"]  # 可能为空
            distance = primary['distance']
            duration = primary['duration']
            distances.append(distance)
            durations.append(duration)
            print(f"[进度] 小区={row['小区名称']}, 距离={distance}米, 时间={duration}秒")
            if secondary:
                sec_distance = secondary['distance']
                sec_duration = secondary['duration']
                sec_distances.append(sec_distance)
                sec_durations.append(sec_durations)
                print(f"[进度] 小区={row['小区名称']}, 备选路线距离={distance}米, 时间={duration}秒")

        except Exception as e:
            # 如果某条目多次重试仍失败，记为 -1 或其他占位值，或自行决定处理方式
            print(f"[错误] 无法获取 {row['小区名称']} 到 {target_address} 的驾车规划: {e}")
            distances.append(-1)
            durations.append(-1)

    df["驾车距离(米)"] = distances
    df["所需时间(秒)"] = durations
    # df["备选驾车距离(米)"] = sec_distances
    # df["备选所需时间(秒)"] = sec_durations
    # 这好像没啥用...
    # 结果另存到 CSV 文件
    df.to_csv(output_csv_path, index=False, encoding="utf-8")
    print(f"处理完成，结果已保存到 {output_csv_path}")


if __name__ == "__main__":
    main()
