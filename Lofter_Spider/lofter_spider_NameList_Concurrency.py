#!/usr/bin/python3
# -*- coding:utf-8 -*-
# author: MikeShine
# date: 2018-07-07
"""Capture pictures from lofter with username."""

import re
import os
import platform

import requests

import time
import random
import redis
import gevent
from gevent import monkey

monkey.patch_all()

r0 = redis.Redis(host='172.16.0.5', port=6379,db=0,decode_responses=True)

def _get_path(username):
    path = {
        'Windows': 'D:/litreily/Pictures/python/lofter/' + username,
        'Linux': '/data/dongxuan/' + username              #  这里是保存图片的文件路径!!!!
    }.get(platform.system())

    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def _get_html(url, data, headers):
    try:
        html = requests.post(url, data, headers = headers)
    except Exception as e:
        print("get %s failed\n%s" % (url, str(e)))
        return None
    finally:
        pass
    return html


def _get_blogid(username):
    try:
        html = requests.get('http://%s.lofter.com' % username)
        id_reg = r'src="http://www.lofter.com/control\?blogId=(.*)"'
        blogid = re.search(id_reg, html.text).group(1)
        print('The blogid of %s is: %s' % (username, blogid))
        return blogid
    except Exception as e:          # 返回收据错误。
        print('get blogid from http://%s.lofter.com failed' % username)
        print('please check your username.')
        return False
        #  exit(1)    #  这里退出了程序。                                             


def _get_timestamp(html, time_pattern):
    if not html:
        timestamp = round(time.time() * 1000)  # first timestamp(ms)
    else:
        timestamp = time_pattern.search(html).group(1)
    return str(timestamp)


def _get_imgurls(username, blog, headers):
    blog_url = 'http://%s.lofter.com/post/%s' % (username, blog)
    blog_html = requests.get(blog_url, headers = headers).text
    imgurls = re.findall(r'bigimgsrc="(.*?)"', blog_html)
    print('Blog\t%s\twith %d\tpictures' % (blog_url, len(imgurls)))
    return imgurls


def _capture_images(imgurl, path):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36'}
    for i in range(1,3):
        try:
            image_request = requests.get(imgurl, headers = headers, timeout = 50)
            if image_request.status_code == 200:
                open(path, 'wb').write(image_request.content)
                break
        except requests.exceptions.ConnectionError as e:
            print('\tGet %s failed\n\terror:%s' % (imgurl, e))
            if i == 1:
                imgurl = re.sub('^http://img.*?\.','http://img.',imgurl)
                print('\tRetry ' + imgurl)
            else:
                print('\tRetry fail')
        except Exception as e:
            print(e)
        finally:
            pass


def _create_query_data(blogid, timestamp, query_number):
    data = {'callCount':'1',
    'scriptSessionId':'${scriptSessionId}187',
    'httpSessionId':'',
    'c0-scriptName':'ArchiveBean',
    'c0-methodName':'getArchivePostByTime',
    'c0-id':'0',
    'c0-param0':'number:' + blogid,
    'c0-param1':'number:' + timestamp,
    'c0-param2':'number:' + query_number,
    'c0-param3':'boolean:false',
    'batchId':'123456'}
    return data


def main():
    # prepare paramters
    while r0.llen("UserName"):   
        username = r0.lpop("UserName")
        if _get_blogid(username):
            blogid = _get_blogid(username)          
            query_number = 40
            time_pattern = re.compile('s%d\.time=(.*);s.*type' % (query_number-1))
            blog_url_pattern = re.compile(r's[\d]*\.permalink="([\w_]*)"') 
            
            # creat path to save imgs
            

            # parameters of post packet
            url = 'http://%s.lofter.com/dwr/call/plaincall/ArchiveBean.getArchivePostByTime.dwr' % username
            data = _create_query_data(blogid, _get_timestamp(None, time_pattern), str(query_number))
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36',
                'Host': username + '.lofter.com',
                'Referer': 'http://%s.lofter.com/view' % username,
                'Accept-Encoding': 'gzip, deflate'
            }

            num_blogs = 0
            num_imgs = 0
            index_img = 0
            print('------------------------------- start line ------------------------------')
            while True:
                html = _get_html(url, data, headers).text
                # get urls of blogs: s3.permalink="44fbca_19a6b1b"
                new_blogs = blog_url_pattern.findall(html)
                num_new_blogs = len(new_blogs)
                num_blogs += num_new_blogs 

                if num_new_blogs == 0:
                        print(username + "没有博客")
                        print('------------------------------- stop line -------------------------------')
                        break
                        
                if num_new_blogs != 0:
                    print('NewBlogs:%d\tTotalBolgs:%d' % (num_new_blogs, num_blogs))
                    # get imgurls from new_blogs
                    imgurls = []
                    for blog in new_blogs:   # newblog中的每一篇blog
                        imgurls.extend(_get_imgurls(username, blog, headers))
                    num_imgs += len(imgurls)


                    if num_imgs<=4:
                        print("Less Than 4 Pics And Skip This User")
                        break     
                    

                    # download imgs
                    if num_imgs > 5:
                        path = _get_path(username)   # 可能之前有path这里会报错
                        job_list = []   #  先搞一个job_List
                        for imgurl in imgurls:
                            index_img += 1    # 第几张图
                            file_name = username + '_' + str(index_img)    
                            paths = '%s/%s.%s' % (path, file_name, "jpg")
                            print('{}\t{}'.format(index_img, paths))
                            job = gevent.spawn(_capture_images, imgurl, paths)
                            job_list.append(job)
                            # _capture_images(imgurl, paths)
                        gevent.joinall(job_list)    #   Here~·~~~
                
                if num_new_blogs != query_number:
                    print('------------------------------- stop line -------------------------------')
                    print('capture complete!')
                    print('captured blogs:%d images:%d' % (num_blogs, num_imgs))
                    # print('download path:' + path)
                    print('-------------------------------------------------------------------------')
                    localtime = time.strftime("%Y-%m-%d %H:%M:%S")
                    print(localtime)
                    break

                data['c0-param1'] = 'number:' + _get_timestamp(html, time_pattern)
                print('The next TimeStamp is : %s\n' % data['c0-param1'].split(':')[1])
                # wait a few second
                time.sleep(random.randint(5,10))
        if not _get_blogid(username):
            pass
if __name__ == '__main__':
    main()
