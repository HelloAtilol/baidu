# -*- coding: utf-8 -*-

import pymysql
import requests
from bs4 import BeautifulSoup
import rebuild_baidu as rbb
import os
import time
import getProxyIP as gpi

# 创建全局变量
# 访问次数
req_num = 1
# 代理列表
free_ip = rbb.getProxy()


# https_free_ip = rbb.getHttpsProxy()


def getTagUrl(cursor):
    """
    获取可以访问成功的tag与url
    :param cursor: 游标
    :return: None
    """
    sql = "SELECT tag, url FROM tag_url WHERE isConnect = 1 or isConnect = 0"
    res = cursor.execute(sql)
    return res


def saveData(cursor, data_dict, primary_key="only_id"):
    """
    将数据保存到数据库
    :param cursor: 数据库游标
    :param data_dict: 存入数据的字典
    :param primary_key: 主键
    :return:
    """
    # 检测数据是否存在
    sqlExit = "SELECT only_id FROM all_content WHERE only_id = '%s' " % (data_dict[primary_key])
    # 执行查找语句
    res = cursor.execute(sqlExit)
    if res:
        print('数据已经存入数据库', data_dict['title'])
    else:
        # 拼接属性名
        cols = ','.join(data_dict.keys())
        # 拼接属性名对应的值
        values = '","'.join(data_dict.values())
        # 插入语句
        sql = "INSERT INTO all_content (%s) VALUES (%s)" % (cols, '"' + values + '"')
        try:
            cursor.execute(sql)
        except pymysql.err.ProgrammingError:
            print(sql)
            os.system("pause")
        # print(data_dict['title'], "****已保存到数据库！")


def updatePageNum(cursor, tag, page_num):
    # 拼接属性名
    cols = ','.join(page_num.keys())
    # 拼接属性名对应的值
    values = str(page_num[cols])
    sql = "UPDATE tag_url SET %s = %s WHERE tag = '%s'" % (cols, values, tag)
    # print(sql)
    cursor.execute(sql)


def selectPage(cursor, tag):
    sql = "SELECT now_num FROM tag_url WHERE tag = '%s'" % tag
    cursor.execute(sql)
    return cursor.fetchone()[0]


def parseUrl(cursor, soup):
    """
    对网页进行解析
    :param cursor: 游标，这里传入游标是为了添加新的tag
    :param soup: beautiful soup对象
    :return: 无返回值，直接保存在数据库
    """
    # 建立空字典
    data_dict = {}
    result = soup.find("ul", {'class': 'wgt-list'})
    # 这里将得到的类当做tag类或者说是beautiful soup类
    all_content = result.find_all("li")
    for content in all_content:
        # 文章名称
        title = content.dl.dt.a.string.replace("\n", "")
        # 文章描述
        describe = content.dl.dd.a.string.replace("\n", "")
        # 文章url
        url = content.dl.dd.a["href"]
        # 文章唯一ID
        article_id = url.replace("http://jingyan.baidu.com/article/", "").replace(".html", "")
        # 有用数
        support = content.dl.find("dd", {'class': 'support'})
        for s in support.strings:
            s_sentence = s
        support_num = s_sentence.replace("有用(", "").replace(")", "")
        # 文章tag
        tags = content.dl.find("dd", {'class': 'tag'}).find_all('a')
        all_tag = ""
        for tag in tags:
            if tag.string is None:
                break
            now_tag = tag.string.replace('\n', '')
            try:
                tag_url = tag["href"]
                rbb.insert_data(cursor, (now_tag, tag_url, 0))
            except KeyError:
                pass
            finally:
                all_tag = all_tag + " " + now_tag
        """
        # 将解析结果打印
        print("title:", title)
        print("url:", url)
        print("article_id:", article_id)
        print("tag:", all_tag, "\tsupport:", support_num)
        print("describe:", describe)
        """
        # 将解析结果保存
        data_dict['title'] = title.replace('"', "“")
        data_dict['url'] = url
        data_dict['only_id'] = article_id
        data_dict['tag'] = all_tag
        data_dict['like_num'] = support_num
        data_dict['description'] = describe.replace('"', "“")
        saveData(cursor, data_dict)


def rebuildRequest(cursor, url, maxTime=100):
    """
    重写request请求，加入代理和访问次数限制
    :param cursor: 游标，此处游标为了获取随机代理IP
    :param url: 访问的url地址
    :param maxTime: 最多访问次数，默认100次，可以传入参数进行限制，避免过度访问
    :return:
    """
    # 声明全局变量
    global req_num
    global free_ip
    i = 1

    while True:
        # 获得随机ip
        random_ip = gpi.getRandomProxy(cursor)
        proxies = {random_ip[2]: random_ip[0] + ":" + str(random_ip[1])}
        try:
            r = requests.get(url, proxies=proxies, allow_redirects=False, timeout=3)
        except Exception:
            # time.sleep(sleep_time)
            # 这里处理代理异常，移除无效ip
            # print(e)
            print("***ip失效一次***")
            print(random_ip[0] + ":" + str(random_ip[1]), "失败次数：", random_ip[3]+1)
            gpi.updateProxy(cursor, (random_ip[0], random_ip[3] + 1))
            continue
        # 加规则，疯狂加规则，防止跳转和拦截！
        # 每十次检查一次是否被拦截
        if req_num % 30 is 0:
            if rbb.isError(url):
                print("访问异常了，请手动解封")
                print("url:", url)
                # 被封了，休息2小时
                print("手动解封之后重新启动程序即可！")
                # time.sleep(3600)
                os.system("pause")
            """
            else:
                print("代理IP被封，暂停5分钟。")
                time.sleep(100)
            """
        # 每访问50次，休息600s
        if req_num % 200 is 0:
            print('正在休息！')
            time.sleep(30)
        req_num += 1
        if r.status_code is 200:
            print('***代理IP***')
            print(random_ip[0] + ":" + str(random_ip[1]))
            print('***第', i, '次访问成功！***')
            return r
        # 超过访问次数，返回None
        i += 1
        if i > maxTime:
            return None
        print('第', i, '次访问失败！')


def requestTagUrl(cursor, data):
    """
    访问tag对应的url，并将页面解析
    :param cursor: 数据库游标
    :param data: 数据，格式为元组(tag, url)
    :return:
    """
    tag = data[0]
    url = data[1]
    print(tag, "***正在访问***", url)
    req = rebuildRequest(cursor, url, 10)
    if req is None:
        rbb.update_data(cursor, (2, tag))
    else:
        part_url = "/tag?tagname=" + tag + "&rn=10&pn="
        # 解析网页
        soup = BeautifulSoup(req.text, "lxml")
        # 解析第一页
        parseUrl(cursor, soup)
        # 获取页面数量
        page = soup.find("div", {'id': 'pg', 'class': 'pg'})
        last_page = page.find_all('a')[-1]
        page_num = int(last_page['href'].lower().replace(part_url, ""))
        updatePageNum(cursor, tag, {'page_num': page_num / 10})
        now_num = selectPage(cursor, tag)
        # 解析之后的页面
        for pg in range(now_num, int(page_num / 10) + 1):
            print('第', pg + 1, "页，正在查询")
            new_url = url + "&rn=10&pn=" + str(pg * 10)
            new_req = rebuildRequest(cursor, new_url)
            t = 1
            while new_req is None:
                new_req = rebuildRequest(new_url)
                t += 1
                if t > 100:
                    updatePageNum(cursor, tag, {'now_num': pg + 1})
                    break
            if t > 100:
                continue
            new_soup = BeautifulSoup(new_req.text, "lxml")
            parseUrl(cursor, new_soup)
            updatePageNum(cursor, tag, {'now_num': pg})


def main():
    # 建立数据库连接
    cursor, conn = rbb.getConnectWithDB()
    # 使用游标获取可以访问的tag与url
    while getTagUrl(cursor):
        tag_url = cursor.fetchone()
        requestTagUrl(cursor, tag_url)
        rbb.update_data(cursor, (3, tag_url[0]))
        conn.commit()
    cursor.close()
    conn.close()


if __name__ == '__main__':
    # time.sleep(3600)
    main()


# 测试代码
def testNewPage():
    url = "https://jingyan.baidu.com/tag?tagName=养发&rn=10&pn=20"
    new_req = requests.get(url)
    new_soup = BeautifulSoup(new_req.text, "lxml")
    print(new_req.status_code)
    print(new_soup.text)
