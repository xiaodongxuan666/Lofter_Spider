
# coding: utf-8
# 这是把Lofter爬虫爬到的文件打包的脚本,每5000个文件打个包，最终每个包的大小大概在250G左右。当前爬到的文件大概在20W个。
# writer：MikeShine
# date: 2018-7-17

import os
import time
from datetime import datetime
import tarfile
import shutil

base = r"/data/donePackage/dongxuan/lofter_"

def package(fname):   
    round_time = 0 
    tmp_List = []

    localtime = time.strftime("%Y-%m-%d %H:%M:%S")
    print(localtime+"  正在遍历文件内目录，需要较长时间，请等待......")
    
    for root, dir, files in os.walk(fname):
         for direction in dir:
            file_path = os.path.join(root, direction)  # 文件路径
            time_file = datetime.utcfromtimestamp (os.path.getmtime(file_path))
            time_now =datetime.utcfromtimestamp(time.time())  # 和当前时间的时间差。  要考虑遍历文件所用的时间。
            time_minus = (time_now - time_file).days
            if time_minus > 2 :  # 2天之前就完成的文件,添加到临时队列
                tmp_List.append(file_path)  

            if len(tmp_List) == 5000:  #到5000个,打包一次
                work_path = base + str(round_time) + '.tar.gz'
                t = tarfile.open(work_path,"w:gz") 
                for file_now in tmp_List:
                    t.add(file_now)
                    # 写一些用于Debug的输出信息
                    localtime = time.strftime("%Y-%m-%d %H:%M:%S")
                    print(localtime + "文件：" + file_now + "已经打包到----" + str(round_time))
                    shutil.rmtree(file_now)
                t.close()
                tmp_List = []  # 打包完成之后清空临时工作列表
                round_time += 1   
    print("打包完成！")


localtime = time.strftime("%Y-%m-%d %H:%M:%S")
print(localtime+ "开始打包......")
package(r'/data/dongxuan')

    

