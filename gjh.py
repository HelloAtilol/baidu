# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import time
import random


# 访问URL
def req(url, i, only_one, free_ip, sleep_time):
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
            if tag.text not in only_one:
                tag_dict[tag.text] = 'https://jingyan.baidu.com' + tag["href"]
                only_one.add(tag.text)
        print(tag_dict.keys())
        return tag_dict, True
    else:
        # 此处可以实现多次访问,设定为3次，每次睡眠时间为3秒
        i += 1
        if i < 5:
            return req(url, i, only_one, free_ip, sleep_time)
        else:
            print("出现跳转，访问失败！", r.history)
            return None, False


def getProxy():
    free_ip = []
    with open("freeProxy.txt", "r") as f:
        for line in f.readlines():
            free_ip.append(line.replace("\n", ""))
    return free_ip


def deal_file(sleep_time, only_one):
    # 获取代理ip数组
    free_ip = getProxy()
    i = 1
    # 通过txt文件读取与保存TAG
    with open("label_list.txt", 'r', encoding='utf-8') as f:
        lv = f.readline()
        while lv is not "":
            # 获取url和label
            print(lv.replace("\n", ""))
            result = lv.split(" ")
            url = result[1]
            only_one.add(result[0])
            # 访问链接并得到字典{"tag":"tag_url"}
            # 每10个休息30秒
            if i % 10 == 0:
                time.sleep(sleep_time)
            tag_dict, isSuccessful = req(url, 0, only_one, free_ip, sleep_time)
            if isSuccessful:
                with open("successful_tag.txt", "a", encoding="utf-8") as fa:
                    fa.write(lv)
                if tag_dict is not None:
                    # 将字典写入到文件,这里每次写入都要保存，不然无法读取后面加入的数据
                    with open("label_list.txt", "a", encoding='utf-8') as a:
                        for tag, tag_url in tag_dict.items():
                            a.write("\n" + tag + " " + tag_url)
            else:
                with open("fail_tag.txt", "a", encoding="utf-8") as fa:
                    fa.write(lv)
            lv = f.readline()
            i += 1


if __name__ == '__main__':

    # 设置睡眠时间
    sleep_time = 60
    # 建立集合，保证访问得到的数据都是唯一的
    only_one = set()
    with open("label_list.txt", 'r', encoding='utf-8') as f1:
        for line in f1.readlines():
            res = line.split(" ")
            tag = res[0]
            if tag not in only_one:
                only_one.add(tag)
    deal_file(sleep_time, only_one)
