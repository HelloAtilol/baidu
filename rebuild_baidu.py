# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import time
import random
import pymysql
import os
import telnetlib


# 建立数据库连接
def getConnectWithDB():
    connect = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        db='baidu_jingyan'
    )
    # 获取游标
    cursor = connect.cursor()
    return cursor, connect


def getProxy():
    free_ip = set()
    with open("freeProxy.txt", "r") as f:
        for line in f.readlines():
            free_ip.add(line.replace("\n", ""))
    return free_ip


def getHttpsProxy():
    https_free_ip = set()
    with open("httpsFreeProxy.txt", "r") as f:
        for line in f.readlines():
            https_ip = line.replace("\n", "")
            https_free_ip.add(https_ip)
    return https_free_ip


def isError(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "lxml")
    if "location.href='/vertify.html'" in soup.text:
        return True
    else:
        return False


# 建立访问连接，访问URL
def req(url, free_ip, i=0):
    tag_dict = {}
    max_size = len(free_ip)
    # 获得随机ip
    try:
        random_ip = free_ip[random.randint(0, max_size)]
    except IndexError:
        random_ip = free_ip[0]
    proxies = {"http": random_ip}
    try:
        r = requests.get(url, proxies=proxies, allow_redirects=False)
        print("代理ip：", random_ip)
    except requests.exceptions.ProxyError:
        # time.sleep(sleep_time)
        # 这里处理代理异常，如果出现代理无法使用，则使用本机地址, 并移除无效ip
        free_ip.remove(random_ip)
        r = requests.get(url, allow_redirects=False)

    # 判断是否跳转
    if r.status_code is 200:
        soup = BeautifulSoup(r.text, "lxml")
        title = soup.select(".wgt-tag dl dt")
        related_tag = soup.select("a.tag")
        print(title[0].text, "第%s次访问成功！！！" % str(i + 1))
        for tag in related_tag:
            tag_dict[tag.text] = 'https://jingyan.baidu.com' + tag["href"]
        print(tag_dict.keys())
        return tag_dict, 1  # 访问成功就设置isConnect为1
    else:
        # 此处可以实现多次访问,设定为5次，无睡眠时间
        i += 1
        if i < 5:
            return req(url, free_ip, i)
        else:
            print("出现跳转，访问失败！")
            # 判断是否已经访问异常
            if isError(url):
                print("访问异常了，请手动解封")
                os.system("pause")
            return None, 2  # 访问失败就设置isConnect为2


def insert_data(cursor, data):
    try:
        sql = "INSERT tag_url (tag,url,isConnect) values ('%s','%s','%d' )"
        cursor.execute(sql % data)
    except pymysql.err.IntegrityError:
        pass


def update_data(cursor, data):
    sql = "UPDATE tag_url SET isConnect = %d WHERE tag = '%s'"
    cursor.execute(sql % data)


# 递归查找所有TAG
def select_tag(cursor, conn, data):
    i = 1
    # 获取代理地址池
    free_ip = getProxy()
    # 打开标签为data的
    select_sql = "SELECT * FROM tag_url WHERE isConnect = %d"
    while True:

        # 每访问十次，休息60s
        if i % 10 == 0:
            print("正在休息！")
            time.sleep(60)
        cursor.execute(select_sql % data)
        result = cursor.fetchone()
        if result is None:
            print(result)
            break
        tag = result[0]
        url = result[1]
        print(tag, '正在查询，url为：', url)
        tag_dict, isSuccessful = req(url, free_ip)
        # 判断是否获取成功

        if tag_dict is not None:
            for new_tag, tag_url in tag_dict.items():
                insert_data(cursor, (new_tag, tag_url, 0))
        update_data(cursor, (isSuccessful, tag))
        conn.commit()
        i += 1


def main():
    # 建立数据库连接
    cursor, conn = getConnectWithDB()
    select_tag(cursor, conn, 0)
    cursor.close()
    conn.close()


if __name__ == '__main__':
    main()
