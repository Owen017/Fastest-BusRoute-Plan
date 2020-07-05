#!E:/python36/python.exe
# -*- coding: utf-8 -*-

import pymysql
import heapq
from collections import defaultdict
db = pymysql.connect("localhost","root","happy123","transport")
cursor = db.cursor()

# CGI处理模块
import cgi
# 创建 FieldStorage 的实例化
form = cgi.FieldStorage() 
# 获取数据
set_hour = form.getvalue('hour')
set_min  = form.getvalue('min')

# 时间滚轮没有转动, 表单传输为None, 默认为当前时间, 在py里设置
# (1)获取当前时间
import datetime
cur = datetime.datetime.now()
nowHour = cur.hour
nowMin = cur.minute
# (2)设定默认时间为当前时间, 由于下文算法中会将时间变为int, 故这里不用作时间的格式化处理
if set_hour==None:
    set_hour = str(nowHour)
    set_min = str(nowMin)
# set_time是下面getConsumeThen方法的参数"上车时间"
set_time = set_hour + ":" + set_min

class Segment:
    def __init__(self, lineid, path):
        # 数据库查询
        sql = "SELECT * FROM path0611 WHERE lineid='{0}' AND path='{1}'".format(lineid,path)
        cursor.execute(sql)
        result = cursor.fetchall()
        # 查询结果分配
        lineid,direction,path,starts = result[0][0], result[0][1], result[0][2], result[0][3]
        ends,linename,nexts,dirname = result[0][5], result[0][7], result[0][8], result[0][9]
        #transfer = result[0][10]
        startt, endt = [], []
        for row in result:
            startt.append(row[4])
            endt.append(row[6])   
        # 类的属性赋值
        self.path = path
        self.lineid = lineid
        self.direction = direction
        self.startstation = starts
        self.starttime = startt
        self.endstation = ends
        self.endtime = endt
        self.linename = linename
        self.nextstation = nexts
        self.dirname = dirname.rstrip('\n')
        # 换成时间放入数据库的方法被废除, 不同线路换乘时间不同, 不能固定下来
        # self.transfer = transfer 
        # upstair/downstair是上车的时间和下车的时间, 在getConsumeNow()/getConsumeThen()里进行赋值
        self.upstair = ""
        self.downstair = ""
    
    # 这里为啥叫Then呢, 因为原来还有个方法是now, 后来删掉, 和Then合并了
    def getConsumeThen(self, st, transfer):
        # 输入时间格式为"xx:xx"
        sth = int(st.split(':')[0])
        stm = int(st.split(':')[1])
        # 拿数据库的时刻表和st参数进行计算
        for i in self.starttime:
            temp = i.split(":")
            starthour = int(temp[0])
            startminu = int(temp[1])
            if sth == starthour:
                if (startminu-transfer) >= stm:
                    # upstair上车时间和downstair下车时间赋值
                    if startminu<10:
                        self.upstair = str(starthour)+":0"+str(startminu)
                    else:
                        self.upstair = str(starthour)+":"+str(startminu)
                    et = self.endtime[self.starttime.index(i)]
                    self.downstair = et
                    # return 上车时间starttime(即i), 下车时间et
                    return i, et
            if sth < starthour:
                # "or (starthour-sth)>1"让距离首班车还有大于1小时的starthour能取到首班车的时间
                if (startminu+60-transfer) >= stm or (starthour-sth)>1:
                    if startminu<10:
                        self.upstair = str(starthour)+":0"+str(startminu)
                    else:
                        self.upstair = str(starthour)+":"+str(startminu)
                    et = self.endtime[self.starttime.index(i)]
                    self.downstair = et
                    return i, et

            ### 问题: 缺少时间验证，如果当前时间过了最后一班的时间就会报错

# 设定方向---------
zjy = 0
# zjy = 1


# route_time_dict: {key: 这条路线的最后到达时刻, value: route信息}
route_time_dict = defaultdict(list)

# 开始程序---------
# 方案1虹桥-南桥汽车站-海湾
# 虹桥到南桥, 虹桥 - 虹桥西交通中心, 可乘坐hq5或hq5b, 虹桥出发耗时8分钟
case1_Hongqiao_Nanqiao_hq5 = Segment('hq5','虹桥到南桥')
case1_result_hq5 = case1_Hongqiao_Nanqiao_hq5.getConsumeThen(set_time,8)
case1_Hongqiao_Nanqiao_hq5b = Segment('hq5b','虹桥到南桥')
case1_result_hq5b = case1_Hongqiao_Nanqiao_hq5b.getConsumeThen(set_time,8)
# 南桥到海湾, 南桥汽车站-南桥汽车站, 可乘坐fx18或fx9, 南桥汽车站本站换乘2分钟
case1_Nanqiao_Haiwan_fx18_A = Segment('fx18', '南桥到海湾')
# fx18两种来源: case1_resultA_fx18(hq5 - fx18), case1_resultB_fx18(hq5b - fx18)
case1_resultA_fx18 = case1_Nanqiao_Haiwan_fx18_A.getConsumeThen(case1_result_hq5[1], 2)
case1_Nanqiao_Haiwan_fx18_B = Segment('fx18', '南桥到海湾')
case1_resultB_fx18 = case1_Nanqiao_Haiwan_fx18_B.getConsumeThen(case1_result_hq5b[1], 2)
case1_Nanqiao_Haiwan_fx9_A = Segment('fx9', '南桥到海湾')
# fx9两种来源: case1_resultA_fx9(hq5 - fx9), case1_resultB_fx9(hq5b - fx9)
case1_resultA_fx9 = case1_Nanqiao_Haiwan_fx9_A.getConsumeThen(case1_result_hq5[1], 2)
case1_Nanqiao_Haiwan_fx9_B = Segment('fx9', '南桥到海湾')
case1_resultB_fx9 = case1_Nanqiao_Haiwan_fx9_B.getConsumeThen(case1_result_hq5b[1], 2)
# 记录路线和对应的Segment类到route_time_dict字典, 方便做最后一步时间对应查找
route_time_dict[(case1_resultA_fx18[1])].append([case1_Hongqiao_Nanqiao_hq5,case1_Nanqiao_Haiwan_fx18_A])
route_time_dict[(case1_resultB_fx18[1])].append([case1_Hongqiao_Nanqiao_hq5b,case1_Nanqiao_Haiwan_fx18_B])
route_time_dict[(case1_resultA_fx9[1])].append([case1_Hongqiao_Nanqiao_hq5,case1_Nanqiao_Haiwan_fx9_A])
route_time_dict[(case1_resultB_fx9[1])].append([case1_Hongqiao_Nanqiao_hq5b,case1_Nanqiao_Haiwan_fx9_B])


# 方案2虹桥-莘庄-南桥汽车站-海湾
# 虹桥到莘庄, 虹桥 - 虹桥西交通中心, 可乘坐xhkx, 虹桥出发耗时8分钟
case2_Hongqiao_Xinzhuang_xhkx = Segment('xhkx', '虹桥到莘庄')
case2_result_xhkx = case2_Hongqiao_Xinzhuang_xhkx.getConsumeThen(set_time,8)
#[xhkxb]是去换乘5号线用的北广场下车方案
#Hongqiao_Xinzhuang_xhkxb = Segment('xhkxb', '虹桥到莘庄')
#result_xhkxb = Hongqiao_Xinzhuang_xhkxb.getConsumeNow(8)
# 莘庄到南桥, 南北广场 - 南桥汽车站, 可乘坐xngs, 南广场换乘南xhkx/xngs 1min
case2_Xinzhuang_Nanqiao_xngs = Segment('xngs', '莘庄到南桥')
# xngs一种来源: resultA_xngs(xhkx - xngs)
case2_result_xngs = case2_Xinzhuang_Nanqiao_xngs.getConsumeThen(case2_result_xhkx[1], 1)
# 南桥到海湾, 南桥汽车站-南桥汽车站, 可乘坐fx18或fx9, 南桥汽车站本站换乘2分钟
case2_Nanqiao_Haiwan_fx18 = Segment('fx18', '南桥到海湾')
# fx18一种来源: rcase2_esultA_fx18(xhkx - xngs - fx18)
case2_result_fx18 = case2_Nanqiao_Haiwan_fx18.getConsumeThen(case2_result_xngs[1], 2)
case2_Nanqiao_Haiwan_fx9 = Segment('fx9', '南桥到海湾')
# fx9一种来源: case2_resultA_fx9(xhkx - xngs - fx9)
case2_result_fx9 = case2_Nanqiao_Haiwan_fx9.getConsumeThen(case2_result_xngs[1], 2)
# 记录路线
route_time_dict[(case2_result_fx18[1])].append([case2_Hongqiao_Xinzhuang_xhkx,case2_Xinzhuang_Nanqiao_xngs,case2_Nanqiao_Haiwan_fx18])
route_time_dict[(case2_result_fx9[1])].append([case2_Hongqiao_Xinzhuang_xhkx,case2_Xinzhuang_Nanqiao_xngs,case2_Nanqiao_Haiwan_fx9])


# 方案3虹桥-莘庄-奉贤新城-海湾
# 虹桥到莘庄, 虹桥 - 虹桥西交通中心, 可乘坐xhkxb在北广场下车, 虹桥出发耗时8分钟
case3_Hongqiao_Xinzhuang_xhkxb = Segment('xhkxb', '虹桥到莘庄')
case3_result_xhkxb = case3_Hongqiao_Xinzhuang_xhkxb.getConsumeThen(set_time,8)
# 莘庄到奉贤新城, 北广场 - 莘庄地铁站, 乘坐5号线, 4min
case3_Xinzhuang_Fengcheng_m5 = Segment('m5', '莘庄到奉城')
case3_result_m5 = case3_Xinzhuang_Fengcheng_m5.getConsumeThen(case3_result_xhkxb[1], 4)
# 奉贤新城到海湾, 奉城地铁站 - 奉城公交站(hs,3min), 奉城地铁站 - 公交南港路站(fx20,fx18,6min)
# 三种路线, 前面都一样, 最后一段hs/ fx20/ fx18的区别罢了 
case3_Fengcheng_Haiwan_hs = Segment('hs', '奉城到海湾')
case3_result_hs = case3_Fengcheng_Haiwan_hs.getConsumeThen(case3_result_m5[1], 3)
case3_Fengcheng_Haiwan_fx18 = Segment('fx18', '奉城到海湾')
case3_result_fx18 = case3_Fengcheng_Haiwan_fx18.getConsumeThen(case3_result_m5[1], 3)
case3_Fengcheng_Haiwan_fx20 = Segment('fx20', '奉城到海湾')
case3_result_fx20 = case3_Fengcheng_Haiwan_fx20.getConsumeThen(case3_result_m5[1], 3)

route_time_dict[(case3_result_hs[1])].append([case3_Hongqiao_Xinzhuang_xhkxb,case3_Xinzhuang_Fengcheng_m5,case3_Fengcheng_Haiwan_hs])
route_time_dict[(case3_result_fx18[1])].append([case3_Hongqiao_Xinzhuang_xhkxb,case3_Xinzhuang_Fengcheng_m5,case3_Fengcheng_Haiwan_fx18])
route_time_dict[(case3_result_fx20[1])].append([case3_Hongqiao_Xinzhuang_xhkxb,case3_Xinzhuang_Fengcheng_m5,case3_Fengcheng_Haiwan_fx20])


# 方案4虹桥-东川路-奉贤新城-海湾
# 虹桥到东川路, 虹桥 - 虹桥西交通中心, 乘坐mh2在东川路地铁站下车, 虹桥出发耗时8分钟
case4_Hongqiao_Dongchuan_mh2 = Segment('mh2', '虹桥到东川')
case4_result_mh2 = case4_Hongqiao_Dongchuan_mh2.getConsumeThen(set_time,8)
# 东川到奉城, 东川路公交站 - 东川路地铁站(m5, 2min)
case4_Dongchuan_Fengcheng_m5 = Segment('m5', '东川到奉城')
case4_result_m5 = case4_Dongchuan_Fengcheng_m5.getConsumeThen(case4_result_mh2[1], 2)
# 奉城到海湾, 同方案3最后一段
case4_Fengcheng_Haiwan_hs = Segment('hs', '奉城到海湾')
case4_result_hs = case4_Fengcheng_Haiwan_hs.getConsumeThen(case4_result_m5[1], 3)
case4_Fengcheng_Haiwan_fx18 = Segment('fx18', '奉城到海湾')
case4_result_fx18 = case4_Fengcheng_Haiwan_fx18.getConsumeThen(case4_result_m5[1], 3)
case4_Fengcheng_Haiwan_fx20 = Segment('fx20', '奉城到海湾')
case4_result_fx20 = case4_Fengcheng_Haiwan_fx20.getConsumeThen(case4_result_m5[1], 3)

route_time_dict[(case4_result_hs[1])].append([case4_Hongqiao_Dongchuan_mh2,case4_Dongchuan_Fengcheng_m5,case4_Fengcheng_Haiwan_hs])
route_time_dict[(case4_result_fx18[1])].append([case4_Hongqiao_Dongchuan_mh2,case4_Dongchuan_Fengcheng_m5,case4_Fengcheng_Haiwan_fx18])
route_time_dict[(case4_result_fx20[1])].append([case4_Hongqiao_Dongchuan_mh2,case4_Dongchuan_Fengcheng_m5,case4_Fengcheng_Haiwan_fx20])


# 方案5虹桥-颛桥-奉贤新城-海湾
# 虹桥到颛桥, 虹桥 - 虹桥西交通中心, 乘坐mh1在颛桥下车, 虹桥出发耗时8分钟
case5_Hongqiao_Zhuanqiao_mh1 = Segment('mh1', '虹桥到颛桥')
case5_result_mh1 = case5_Hongqiao_Zhuanqiao_mh1.getConsumeThen(set_time,8)
# 颛桥到奉城, 颛桥公交站 - 颛桥地铁站(m5, 4min)
case5_Zhuanqiao_Fengcheng_m5 = Segment('m5', '颛桥到奉城')
case5_result_m5 = case5_Zhuanqiao_Fengcheng_m5.getConsumeThen(case5_result_mh1[1], 4)
# 奉城到海湾, 同方案3最后一段
case5_Fengcheng_Haiwan_hs = Segment('hs', '奉城到海湾')
case5_result_hs = case5_Fengcheng_Haiwan_hs.getConsumeThen(case5_result_m5[1], 3)
case5_Fengcheng_Haiwan_fx18 = Segment('fx18', '奉城到海湾')
case5_result_fx18 = case5_Fengcheng_Haiwan_fx18.getConsumeThen(case5_result_m5[1], 3)
case5_Fengcheng_Haiwan_fx20 = Segment('fx20', '奉城到海湾')
case5_result_fx20 = case5_Fengcheng_Haiwan_fx20.getConsumeThen(case5_result_m5[1], 3)

route_time_dict[(case5_result_hs[1])].append([case5_Hongqiao_Zhuanqiao_mh1,case5_Zhuanqiao_Fengcheng_m5,case5_Fengcheng_Haiwan_hs])
route_time_dict[(case5_result_fx18[1])].append([case5_Hongqiao_Zhuanqiao_mh1,case5_Zhuanqiao_Fengcheng_m5,case5_Fengcheng_Haiwan_fx18])
route_time_dict[(case5_result_fx20[1])].append([case5_Hongqiao_Zhuanqiao_mh1,case5_Zhuanqiao_Fengcheng_m5,case5_Fengcheng_Haiwan_fx20])


# 方案6虹桥-莘庄-环城东路-海湾
# 虹桥到莘庄, 虹桥 - 虹桥西交通中心, 可乘坐xhkxb在北广场下车, 虹桥出发耗时8分钟
case6_Hongqiao_Xinzhuang_xhkxb = Segment('xhkxb', '虹桥到莘庄')
case6_result_xhkxb = case6_Hongqiao_Xinzhuang_xhkxb.getConsumeThen(set_time,8)
# 莘庄到环城东路, 北广场 - 莘庄地铁站, 乘坐5号线, 4min
case6_Xinzhuang_Huandong_m5 = Segment('m5', '莘庄到环东')
case6_result_m5 = case6_Xinzhuang_Huandong_m5.getConsumeThen(case6_result_xhkxb[1], 4)
# 环城东路到海湾, 环城东路地铁站 - 环城东路航南公路公交站(fx29,5min)
case6_Huandong_Haiwan_fx29 = Segment('fx29', '环东到海湾')
case6_result_fx29 = case6_Huandong_Haiwan_fx29.getConsumeThen(case6_result_m5[1], 5)

route_time_dict[(case6_result_fx29[1])].append([case6_Hongqiao_Xinzhuang_xhkxb,case6_Xinzhuang_Huandong_m5,case6_Huandong_Haiwan_fx29])


# 方案7虹桥-东川路-环城东路-海湾
# 虹桥到东川路, 虹桥 - 虹桥西交通中心, 乘坐mh2在东川路地铁站下车, 虹桥出发耗时8分钟
case7_Hongqiao_Dongchuan_mh2 = Segment('mh2', '虹桥到东川')
case7_result_mh2 = case7_Hongqiao_Dongchuan_mh2.getConsumeThen(set_time,8)
# 东川到环东, 东川路公交站 - 东川路地铁站(m5, 2min)
case7_Dongchuan_Huandong_m5 = Segment('m5', '东川到环东')
case7_result_m5 = case7_Dongchuan_Huandong_m5.getConsumeThen(case7_result_mh2[1], 2)
# 环东到海湾, 同方案6最后一段
case7_Huandong_Haiwan_fx29 = Segment('fx29', '环东到海湾')
case7_result_fx29 = case7_Huandong_Haiwan_fx29.getConsumeThen(case7_result_m5[1], 5)

route_time_dict[(case7_result_fx29[1])].append([case7_Hongqiao_Dongchuan_mh2,case7_Dongchuan_Huandong_m5,case7_Huandong_Haiwan_fx29])


# 方案8虹桥-颛桥-环城东路-海湾
# 虹桥到颛桥, 虹桥 - 虹桥西交通中心, 乘坐mh1在颛桥下车, 虹桥出发耗时8分钟
case8_Hongqiao_Zhuanqiao_mh1 = Segment('mh1', '虹桥到颛桥')
case8_result_mh1 = case8_Hongqiao_Zhuanqiao_mh1.getConsumeThen(set_time,8)
# 颛桥到环东, 颛桥公交站 - 颛桥地铁站(m5, 4min)
case8_Zhuanqiao_Huandong_m5 = Segment('m5', '颛桥到环东')
case8_result_m5 = case8_Zhuanqiao_Huandong_m5.getConsumeThen(case8_result_mh1[1], 4)
# 环东到海湾, 同方案6最后一段
case8_Huandong_Haiwan_fx29 = Segment('fx29', '环东到海湾')
case8_result_fx29 = case8_Huandong_Haiwan_fx29.getConsumeThen(case8_result_m5[1], 5)

route_time_dict[(case8_result_fx29[1])].append([case8_Hongqiao_Zhuanqiao_mh1,case8_Zhuanqiao_Huandong_m5,case8_Huandong_Haiwan_fx29])



timelistNo = [case1_resultA_fx18[1], case1_resultB_fx18[1], case1_resultA_fx9[1], case1_resultB_fx9[1], case2_result_fx18[1], case2_result_fx9[1], case3_result_hs[1], case3_result_fx18[1], case3_result_fx20[1], case4_result_hs[1], case4_result_fx18[1], case4_result_fx20[1], case5_result_hs[1], case5_result_fx18[1], case5_result_fx20[1], case6_result_fx29[1], case7_result_fx29[1], case8_result_fx29[1]]
timelist = []
for i in timelistNo:
    if int(i.split(':')[0]) < 4:
        continue
    else:
        timelist.append(i)

# calculTime()获取输入时间列表中值最小的5个, 以[str,str,str]形式返回
def calculTime(timelist):
    timesumList = []
    minRouteList = []
    for i in timelist:
        timesum = (int(i.split(':')[0]))*60 + int(i.split(':')[1])#h*60+m
        timesumList.append(timesum)
    min_num_index_list = map(timesumList.index, heapq.nsmallest(5, timesumList))
    for i in min_num_index_list:
        minRouteList.append(timelist[i])
    return minRouteList

db.close()

mintime = calculTime(timelist)
# 去重保持顺序不变
mintime = sorted(set(mintime),key=mintime.index)


    
def showRoute(timeStr):
    length = len(route_time_dict[timeStr])
    if length == 1:
        for i in route_time_dict[timeStr]:
            counti = len(i)
            for j in i:
                print('<h4>{}</h4>'.format("乘坐[{}],方向:{}".format(j.linename,j.dirname)))
                print('<h4>{}</h4>'.format("上车时间:{}, 上车站:{}".format(j.upstair,j.startstation)))
                print('↓')
                print('<h4>{}</h4>'.format("预计到站时间:{}, 下车站:{}".format(j.downstair,j.endstation)))
                # 通过counti来控制输出换乘符号←→
                counti -= 1
                if counti > 0:
                    print('←→')

    else:
    	# 多种相同时间方案
        for i in route_time_dict[timeStr]:
            counti = len(i)
            length -= 1
            for j in i:
                print('<h4>{}</h4>'.format("乘坐[{}],方向:{}".format(j.linename,j.dirname)))
                print('<h4>{}</h4>'.format("上车时间:{}, 上车站:{}".format(j.upstair,j.startstation)))
                print('↓')
                print('<h4>{}</h4>'.format("预计到站时间:{}, 下车站:{}".format(j.downstair,j.endstation)))
                counti -= 1
                if counti > 0:
                    print('←→')
            if length != 0:
                print('<h4>或</h4>')
            


print ("Content-type:text/html")
print ()                             # 空行，告诉服务器结束头部
print ('<html>')
print ('<head>')
print ('<title>CGI实现网页执行py公交路径算法</title>')
print ("<script src='https://cdn.staticfile.org/jquery/1.10.2/jquery.min.js'></script>")
# 这里的JQuery多个滑窗写法参考runoob+https://blog.csdn.net/yqyily/article/details/51690894
print ("""
<style>
div.flip
{
    padding:5px;
    text-align:center;
    background-color:#3cb371;
    border:solid 1px #c3c3c3;
}
div.panel
{
    padding:5px;
    text-align:center;
    background-color:white;
    border:solid 1px #c3c3c3;
}
div.panel
{
	padding:30px;
	display:none;
}
</style>
	""")
print ("""
<script> 
$(document).ready(function(){
	$(".flip").click(function(){
		$(".panel:eq(" + $(this).index(".flip") + ")").slideToggle("slow");
	});
});
</script>
	""")
print ('</head>')
print ('<body>')
# 格式化分钟数字格式, 避免出现展示页面中当前时间为"14:9"的情况
if (int(set_min)<10):
	if (int(set_min)==0):
		set_min = "00"
	else:
		set_min = '0' + str(set_min)
print ("<h2>设定出发时间为{}:{}, 可快速抵达上师大奉贤校区的方案如下:</h2>".format(set_hour,set_min))
countprint = 0
# 没有方案时, mintime为空列表, 输出无可达方案
if mintime == []:
    print("<h3>没有可达方案, 明天再出发吧。</h3>")
# 所有可取方案都在mintime里, 一个方案一个for
for count in mintime:
    countprint += 1
    print('<div class="flip"><h2 style="color:white;">{}</h2><h3>预计到达时间{}</h3></div>'.format("第{}快的方案".format(countprint),count))
    print("<div class='panel'>")
    showRoute(count)
    print("</div>")
print ('</body>')
print ('</html>')
