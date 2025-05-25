import re, os
import json
import requests
import time, glob
import csv
from collections import Counter
# read csv
def write_csv(filepath, data, head=None):
    if head:
        data = [head] + data
    with open(filepath, mode='w', encoding='UTF-8-sig', newline='') as f:
        writer = csv.writer(f)
        for i in data:
            writer.writerow(i)
# write csv
def read_csv(filepath):
    data = []
    if os.path.exists(filepath):
        with open(filepath, mode='r', encoding='gbk') as f:
            lines = csv.reader(f)  # #此处读取到的数据是将每行数据当做列表返回的
            for line in lines:
                data.append(line)
        return data
    else:
        print('filepath is wrong：{}'.format(filepath))
        return []
def openUrl(_url):
    # 设置请求头 request header
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    }
    response = requests.get(_url, headers=headers)
    if response.status_code == 200:  # 如果状态码为200，寿命服务器已成功处理了请求，则继续处理数据
        return response.content
    else:
        return None
def getPanoId(_lng, _lat):
    # 获取百度街景中的svid get svid of baidu streetview
    url = "https://mapsv0.bdimg.com/?&qt=qsdata&x=%s&y=%s&l=17.031000000000002&action=0&mode=day&t=1530956939770" % (
        str(_lng), str(_lat))
    response = openUrl(url).decode("utf8")
    if (response == None):
        time.sleep(600)
    reg = r'"id":"(.+?)",'
    pat = re.compile(reg)
    try:
        svid = re.findall(pat, response)[0]
        return svid
    except:
        return None

def wgs2bd09mc(wgs_x, wgs_y):
    # to:5是转为bd0911，6是转为百度墨卡托
    url = 'http://api.map.baidu.com/geoconv/v1/?coords={}+&from=1&to=6&output=json&ak={}'.format(
        wgs_x + ',' + wgs_y,
        'IsOeKbOXHm8Tsz0MWYCm07q4UeNGNIL2'
    )
    # print(url)
    res = openUrl(url).decode()
    temp = json.loads(res)
    bd09mc_x = 0
    bd09mc_y = 0
    if temp['status'] == 0:
        bd09mc_x = temp['result'][0]['x']
        bd09mc_y = temp['result'][0]['y']

    return bd09mc_x, bd09mc_y

from tqdm import tqdm
if __name__ == "__main__":
    root = r'.\dir'
    read_fn = r'SVI12.csv'
    results = []
    # 读取 csv 文件
    data = read_csv(os.path.join(root, read_fn))
    # 记录 header
    header = data[0]
    # 去掉 header
    data = data[1:]
    count = 1
    for i in tqdm(range(len(data)), desc="处理进度", ncols=100):
        try:
            wgs_x, wgs_y = data[i][2], data[i][3]
            bd09mc_x, bd09mc_y = wgs2bd09mc(wgs_x, wgs_y)
            svid = getPanoId(bd09mc_x, bd09mc_y)
            url = f"https://mapsv0.bdimg.com/?qt=sdata&sid={svid}&pc=1"
            response = requests.get(url)
            json_data = response.json()
            date_str = json_data['content'][0]['Date']
            results.append({
                'id': data[i][0],
                'name': data[i][1],
                'lon': wgs_x,
                'lat': wgs_y,
                'date': date_str
            })
            time.sleep(0.05)
        except Exception as e:
            print(e)
            continue
    # 保存结果到 CSV 文件
    output_csv = 'panorama_dates12W.csv'
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'name', 'lon', 'lat', 'date'])
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    # 统计月份占比
    month_counts = Counter()
    for row in results:
        date_str = row['date']
        month = date_str[4:6]  # 例如 "20221114" 提取 "11"
        month_counts[month] += 1
    total = sum(month_counts.values())
    print("\n月份占比：")
    for month in sorted(month_counts):
        count = month_counts[month]
        percent = count / total * 100
        print(f"{month}月: {count} 次，占比 {percent:.2f}%")