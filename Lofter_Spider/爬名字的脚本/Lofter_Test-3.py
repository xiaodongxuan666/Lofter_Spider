
# coding: utf-8

# In[50]:


#!/usr/bin/python3
# -*- coding:utf-8 -*-
# author: MikeShine
# date: 2018.06
"""从已知lofter的UserName获得所有关联的UserName
****************************************************
之后就是把所有的得到的UserName全部遍历一遍，用爬每个User所有相册的方法"""

import re
import os
import platform

import requests

import time
import random
import redis

'''
1. 生成或更新归档页请求数据(主要是指username)
2. 模拟归档页面发送POST请求(这里的主要问题是Timestamp)
3. 解析响应数据并获取博客链接(直接Post请求回来之后拿到源码，源码中就可以拿到博客位置)
4. 逐一爬取博客内容
5. 解析博客内容并获取图片链接
6. 逐一下载图片至本地
'''
r1 = redis.Redis(host='127.0.0.1', port=6379,db=3,decode_responses=True)
r2 = redis.Redis(host='127.0.0.1', port=6379,db=4,decode_responses=True)



# In[51]:



def _get_html(url, data, headers):  # 抓包来做的
    try:
        html = requests.post(url, data, headers = headers)    
    except Exception as e:   # Exception 是常规错误的基类
        print("get %s failed\n%s" % (url, str(e)))    # 把这个错误打印出来
        return None
    finally:
        pass
    return html



# In[52]:



def _get_blogid(username):     # 获得每一篇博客的ID
    try:
        html = requests.get('http://%s.lofter.com' % username)   # 拿到个人主页
        id_reg = r'src="http://www.lofter.com/control\?blogId=(.*)"'   
        blogid = re.search(id_reg, html.text).group(1)       # 只匹配一次
        print('The blogid of %s is: %s' % (username, blogid))
        return blogid
    except Exception as e:
        print('get blogid from http://%s.lofter.com failed' % username)
        print('please check your username.')
        exit(1)


# In[53]:



def _get_timestamp(html, time_pattern):   
    if not html:     #首次请求的时间戳
        timestamp = round(time.time() * 1000)  # 本地时间戳，13位的ms时间戳
    else:
        timestamp = time_pattern.search(html).group(1)
    return str(timestamp)




# In[54]:


def _create_query_data(blogid, timestamp, query_number):    #发送请求表单参数
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


# In[55]:


def _get_username_newblog(userName, blog, headers):   # 从新的user的博客里面拿userName
    blog_url = 'http://%s.lofter.com/post/%s' % (userName, blog)
    print(blog_url)
    html = requests.get(blog_url, headers = headers).text
    #下面找 postid
    postId_patn = re.compile('src="http://www.lofter.com/control.*?blogId=.*?postId=(.*?)"')
    postId = re.findall(postId_patn, html)
    print(postId)
    hot_patn = re.compile(r'热度[(](.*?)[)]')    # 发布的博客里面的热度标签  和精选推荐页面的不一样
    hotNum = re.findall(hot_patn,html)  
    
    localtime = time.strftime("%Y-%m-%d %H:%M:%S")
    print(localtime)                             
    print(hotNum)                                               
    userName=[]
    if len(hotNum)==0:    # 如果没有匹配到hotNum，也就是说这个博文没有热度的时候
        return userName
    if len(hotNum)!=0:    # 有热度的时候
        for i in range(0,int(hotNum[0]),50):   # 就算拿了两个也没关系，只取第一个
            getUser_Url = "http://loftermrjx.lofter.com/morenotes?postid=%s&offset=%s"%(postId[0],i)   # 这里postId只有一个
            user_Html = requests.get(getUser_Url, headers = headers).text
            userName_patn = re.compile(r'<span class="action">\r\n\t\t\t\t\t<a href="http://(.*?).lofter.com/"')
            for names in re.findall(userName_patn, user_Html):
                userName.append(names)
    return userName

# username = 'xujiabang'
# headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36',
#         'Host': username + '.lofter.com',
#         'Referer': 'http://%s.lofter.com/view' % username,
#         'Accept-Encoding': 'gzip, deflate'
#     } 
# blog = '1e767c4e_11bac8e1'
# namelist = _get_username_newblog(username,blog,headers = headers)
# namelist
    
 


# In[56]:


def _get_name_loop(nameList):   # 得到nameList里面用户的所有关联的用户名
    nameSet = []
    i = 0
    for names in nameList:
        username = names
        blogid = _get_blogid(username)
        #  下面就是一个用户的主页里面抓名字
        query_number = 40
        time_pattern = re.compile('s%d\.time=(.*);s.*type' % (query_number-1))    # 时间的正则形式  是包含在返回的数据包里面的
        blog_url_pattern = re.compile(r's[\d]*\.permalink="([\w_]*)"') 
        
        url = 'http://%s.lofter.com/dwr/call/plaincall/ArchiveBean.getArchivePostByTime.dwr' % username       # 这个是抓包的服务器地址
        data = _create_query_data(blogid, _get_timestamp(None, time_pattern), str(query_number))
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36',
            'Host': username + '.lofter.com',
            'Referer': 'http://%s.lofter.com/view' % username,
            'Accept-Encoding': 'gzip, deflate'
        }
        num_blogs = 0
        while True:  # 主页里面的所有都抓
            html = _get_html(url, data, headers).text      
            new_blogs = blog_url_pattern.findall(html)     # 找出blog的相对路径
            print(new_blogs)    #这里已经得到了这个用户最开始blog的相对地址了
            
            num_new_blogs = len(new_blogs)
            num_blogs += num_new_blogs 

            
            if num_new_blogs == 0:
                print(username + "没有博客")
                print('-------------------------------------------------------------------------')
                break
                
            if num_new_blogs != 0:    
                print('NewBlogs:%d\tTotalBolgs:%d' % (num_new_blogs, num_blogs))
                for blogs in new_blogs:   #每一篇博客  都爬名字
                    new_name = _get_username_newblog(username, blogs, headers)   # 这里得到了new_name 的 List
                    for names in new_name:   # 就算是空的也不会报错，所以不用debug
                        r2.sadd("userName",names)  # 写到Redis的Set里面

            if num_new_blogs != query_number:    # 没有新的Blog了    
                print('Name Capture completed for user:'+ username)
                print('-------------------------------------------------------------------------')
                break     #没有新的Blog就跳出循环了，不再无限循环了,不然就更新时间戳，继续抓包

            data['c0-param1'] = 'number:' + _get_timestamp(html, time_pattern)   # 更新时间戳
            time.sleep(random.randint(1,5))    # Sec，下一次发包前等一下。
            


# In[57]:


L = r1.smembers("userName")
_get_name_loop(L)


# In[ ]:





# In[ ]:


# 被block掉之后大概 5mins就可以访问了

