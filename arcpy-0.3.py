#!/usr/bin/env python
# -*- coding:utf-8 -*-
# ---------------------------------------------------------------------------
# 修改@泡菜老司机
# Reference:
# python2.7
"""
Description:
本工具基于ArcGIS自带arcpy库实现
版本@0.2
1.可使用命令行导出文件了
[直接运行：python arcpy-0.2.py C:\Downloads\yumiko-arcpy --core 4 --res 300 --output_folder ./output_folder]

版本@0.3
1.可通过自动化读取配置文件批量输出图片
[首次配置：python arcpy-0.3.py --configure]
[直接运行：python arcpy-0.3.py]
"""
# ---------------------------------------------------------------------------
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
if sys.version_info[0] == 2:
    import ConfigParser as configparser
else:
    import configparser

import arcpy
import os
import time
from multiprocessing import Process
import argparse
# import ConfigParser as configparser
 
 
def make_chunk(data_list, chunk_num):
    """将列表（data_list）中的元素平均分配多个子列表
        such as:
            i_list = [1, 34, 3, 67, 8, 98, 39, 98, 34, 3, 67, 8, 98, 39, 98, 34,
                 6, 67, 8, 98, 39, 98, 34, 3, 67, 8 , 34, 3, 67, 8, 98, 39, 98,
                 98, 39, 98, 34, 3, 67, 8, 98, 39, 98, 34, 3, 67, 8, 98, 39, 98,
                 8, 98, 39, 98, 34, 3, 67 ]
            result_list = data_distribute(i_list,6)
 
    data_list{List}: 主要数据列表
    chunk_num{Int}:  组块数（子列表个数）
    :return{List}:  返回两个列表：一个包含所有子列表的列表，一个信息组成的列表
    """
    msg_info = []
     
    def sub_list(main_list, l_len):
        """选择
        :param main_list: {List} 父列表，我们的主要列表
        :param l_len: {Int} 切片长度，使用pop方法
        :return: {List} son 返回一个子列表
        """
        # son 子列表
        son = []
        for ii7 in xrange(l_len):
            son.append(main_list.pop())
        return son
     
    # 顺序反向，因为pop()取最后一位，且比pop(0)快
    data_list.reverse()
    # 包含所有子列表的列表
    result_groups = []
    lenn = len(data_list)
    # print("list_lence:", lenn
    # 分为core组，slice_amount为每组的数量
    slice_amount = lenn // chunk_num
    # print("slice_count:", slice_amount
    for i in xrange(chunk_num):
        # 以core为长度的一个切片
        l_slice = sub_list(data_list, slice_amount)
        # print("one_slice:", l_slice)
        result_groups.append(l_slice)
    # remained_item_amount 主要数据列表中剩余的元素的个数
    remained_item_amount = lenn - slice_amount * chunk_num
    msg1 = "remained_item:{0} ; remained_item_amount:{1}".format(
        data_list, remained_item_amount)
    # print(msg1)
    # 将主要列表中的值取完才结束
    while data_list:
        for i in xrange(remained_item_amount):
            item = data_list.pop()
            result_groups[i].append(item)
    # print("result_groups:",result_groups
    j = 0
    for i in result_groups:
        i_len = len(i)
        info = "Chunk's count: {}".format(i_len)
        print(info)
        msg_info.append(info)
        j += i_len
    info = "total: {}".format(j)
    print(info)
    print("@" * 50)
    msg_info.append(info)
    return result_groups, msg_info
 
 
def address_clip(mxds, process_core):
    """
    从文件夹中选出mxd文档，将全部mxd地址划分为几个切片然后装进列表中备用
    :param process_core: 运行进程数量
    :param mxds:需要出图的mxd文档的路径
    :return: slices_set 包含多个 地址列表的切片包 的列表（列表的列表）
    其他: mxdpath_list = [] # 所有地址的列表
    """
    # global slices_set
    # slices_set = [] # 初始化列表，避免程序二次运行时重复出图
    mxdpaths = []
    for a_mxd in os.listdir(mxds):
        if a_mxd[-3:].lower() == 'mxd':
            mxd_path = os.path.join(mxds, a_mxd)
            mxdpaths.append(mxd_path)  # 将筛选的mxd路径加入列表
     
    slices_set = make_chunk(mxdpaths, process_core)
    return slices_set  # 包含多个 地址列表的切片包 的列表（列表的列表）
 
 
def export_jpeg(path_slice_set, res, output_folder):
    arcpy.env.overwriteOutput = True
    for one_path in path_slice_set:
        mxd1 = arcpy.mapping.MapDocument(one_path)
        output_path = os.path.join(output_folder, os.path.basename(one_path)[:-3] + 'jpg')
        arcpy.mapping.ExportToJPEG(mxd1, output_path, resolution=res)
        del mxd1
        info = "{} 完成! 进程ID:{}\n".format(os.path.basename(one_path), os.getpid())
        print(info)

def main_function(args):
    sets_lists, msg = address_clip(args.path, args.core)
    for a_msg in msg:
        print(a_msg + ";\n")
    for set_li in sets_lists:
        time.sleep(0.5)
        # 开启多进程
        p = Process(target=export_jpeg, args=(set_li, args.res, args.output_folder))
        p.deamon = True
        p.start()

def configure(args):
    config = configparser.ConfigParser()
    config.read('config.ini')

    if not config.has_section('Settings'):
        config.add_section('Settings')

    config.set('Settings', 'path', args.path)
    config.set('Settings', 'core', str(args.core))
    config.set('Settings', 'res', str(args.res))
    config.set('Settings', 'output_folder', args.output_folder)

    with open('config.ini', 'w') as config_file:
        config.write(config_file)


def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')

    if not config.has_section('Settings'):
        return None

    path = config.get('Settings', 'path')
    core = int(config.get('Settings', 'core'))
    res = int(config.get('Settings', 'res'))
    output_folder = config.get('Settings', 'output_folder')

    return path, core, res, output_folder


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='使用自定义分辨率和输出文件夹导出MXD文件为JPEG图片。')
    parser.add_argument('--configure', action='store_true', help='配置参数设置。')
    parser.add_argument('--showconfig', action='store_true', help='显示当前配置。')
    parser.add_argument('--showhelp', '--fish', action='help', default=argparse.SUPPRESS, help='python arcpy.py input_folder --core 4 --res 300 --output_folder ./output_folder')

    args = parser.parse_args()

if args.configure:
    # 使用 raw_input() 来接收输入
    path = raw_input('请输入包含MXD文件的文件夹路径: ')
    path = path.decode(sys.stdin.encoding)  # 使用系统的编码来解码
    core = int(raw_input('请输入要使用的CPU核心数（默认为4）: ') or 4)
    res = int(raw_input('请输入JPEG导出的分辨率（默认为300）: ') or 300)
    output_folder = raw_input('请输入导出的JPEG图片的输出文件夹（默认为./output）: ')
    output_folder = output_folder.decode(sys.stdin.encoding) if output_folder else u'./output'

    args.path = path
    args.core = core
    args.res = res
    args.output_folder = output_folder

    configure(args)
elif args.showconfig:
    config_values = read_config()

    if config_values:
        path, core, res, output_folder = config_values
        print('当前Yumiko-arcpy配置:')
        print('输入路径:', path)
        print('CPU核心数:', core)
        print('分辨率:', res)
        print('输出文件夹:', output_folder)
    else:
        print('未找到配置。请运行脚本时使用 --configure 选项设置参数。')
else:
    if not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)

    main_function(args)
