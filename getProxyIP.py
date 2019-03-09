# -*- coding: utf-8 -*-

import pymysql
import urllib.request
import urllib
import re
import time
import random
import socket
import threading
import rebuild_baidu as rbb
import requests


def getConnectionWithDB():
    connect = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        db='baidu_jingyan'
    )
    # 获取游标
    cursor = connect.cursor()
    return cursor, connect


def getRandomProxy(cursor):
    sql = "SELECT * FROM proxies_ip WHERE isConnect < 5"
    res = cursor.execute(sql)
    if res > 10:
        random_proxy = random.sample(cursor.fetchall(), 1)[0]
        return random_proxy
    else:
        print("正在更新代理IP池！")
        main()
        return getRandomProxy(cursor)


def updateProxy(cursor, data):
    sql = "UPDATE proxies_ip SET isConnect = %s WHERE proxy_ip = '%s'" % (int(data[1]), data[0])
    cursor.execute(sql)


def deleteProxy(cursor, data):
    sql = "DELETE FROM  proxies_ip WHERE proxy_ip = '%s'" % data
    cursor.execute(sql)


def insertProxy(cursor, proxy_data, primary_key="proxy_ip"):
    # 检测数据是否存在
    sqlExit = "SELECT proxy_ip FROM proxies_ip WHERE proxy_ip = '%s' " % (proxy_data[primary_key])
    # 执行查找语句
    res = cursor.execute(sqlExit)
    if res:
        print('数据已经存入数据库', proxy_data['proxy_ip'])
    else:
        # 拼接属性名
        cols = ','.join(proxy_data.keys())
        # 拼接属性名对应的值
        values = '","'.join(proxy_data.values())
        # 插入语句
        sql = "INSERT INTO proxies_ip (%s) VALUES (%s)" % (cols, '"' + values + '"')
        try:
            cursor.execute(sql)
        except pymysql.err.ProgrammingError:
            print(sql)


def getProxy(proxy_type, ip_pool):
    origin_pool = []
    for page in range(1, 6):
        # url = 'http://ip84.com/dlgn/' + str(page)
        free_ip = random.sample(ip_pool, 1)[0]
        url = 'http://www.xicidaili.com/nn/' + str(page)  # 西刺代理
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64)"}
        """
        proxy_support = urllib.request.ProxyHandler({"http": free_ip})
        opener = urllib.request.build_opener(proxy_support)
        urllib.request.install_opener(opener)
        """
        try:
            req = requests.get(url, headers=headers, proxies={"http": free_ip}, timeout=3)
        except Exception:
            ip_pool.remove(free_ip)
            print(free_ip)
            getProxy(proxy_type, ip_pool)
            break
        print(req.text)
        """
        request = urllib.request.Request(url=url, headers=headers)
        response = urllib.request.urlopen(request)
        content = response.read().decode('utf-8')
        """
        print('get page', page)
        pattern = re.compile('<td>(\d.*?)</td>')  # 截取<td>与</td>之间第一个数为数字的内容
        ip_page = re.findall(pattern, str(req.text))
        origin_pool.extend(ip_page)
        time.sleep(random.choice(range(1, 3)))

    # 将解析的数据规范为dict
    ip_pool = []
    for i in range(0, len(origin_pool), 4):
        ip_pool.append({"proxy_ip": str(origin_pool[i]), "proxy_port": str(origin_pool[i + 1]),
                        "proxy_type": proxy_type, "isConnect": "1"})
    return ip_pool


# 验证代理IP有效性的方法
def checkProxy(lock, data):
    socket.setdefaulttimeout(5)  # 设置全局超时时间
    url = "https://jingyan.baidu.com/"  # 打算爬取的网址
    proxy_data = {data["proxy_type"]: data["proxy_ip"] + ":" + data["proxy_port"]}
    try:
        proxy_support = urllib.request.ProxyHandler(proxy_data)
        opener = urllib.request.build_opener(proxy_support)
        opener.addheaders = [("User-Agent", "Mozilla/5.0 (Windows NT 10.0; WOW64)")]
        urllib.request.install_opener(opener)
        res = urllib.request.urlopen(url).read()
        lock.acquire()  # 获得锁
        data["isConnect"] = "0"
        print(data["proxy_ip"], "已更新/添加到数据库！")
        lock.release()  # 释放锁
    except Exception:
        lock.acquire()
        # print(proxy_data, e)
        lock.release()


def multiCheck(ip_pool):
    lock = threading.Lock()  # 建立一个锁
    threads = []
    for proxy_data in ip_pool:
        thread = threading.Thread(target=checkProxy, args=[lock, proxy_data])
        threads.append(thread)
        thread.start()
    # 阻塞主进程，等待所有子线程结束
    for thread in threads:
        thread.join()


def checkOldProxy(cursor):
    sql = "SELECT * FROM proxies_ip WHERE isConnect >= 5"
    res = cursor.execute(sql)
    if res:
        old_ip_pool = []
        for r in cursor.fetchall():
            old_ip_pool.append({"proxy_ip": r[0], "proxy_port": str(r[1]),
                                "proxy_type": r[2], "isConnect": "1"})
        multiCheck(old_ip_pool)
        for origin_ip in old_ip_pool:
            if origin_ip["isConnect"] is 0:
                updateProxy(cursor, (origin_ip["proxy_ip"], origin_ip["isConnect"]))
            else:
                deleteProxy(cursor, origin_ip["proxy_ip"])


def main():
    cursor, conn = getConnectionWithDB()
    checkOldProxy(cursor)
    conn.commit()
    ip_pool = getProxy("https", rbb.getProxy())
    multiCheck(ip_pool)
    for ip_data in ip_pool:
        if ip_data["isConnect"] is "0":
            insertProxy(cursor, ip_data)
    conn.commit()
    cursor.close()
    conn.close()


def someTest():
    cursor, conn = getConnectionWithDB()
    getRandomProxy(cursor)
    cursor.close()
    conn.close()


if __name__ == '__main__':
    main()
    # someTest()
    # checkOldProxy()
