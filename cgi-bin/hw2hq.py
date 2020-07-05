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
# zjy = 0
zjy = 1

# route_time_dict: {key: 这条路线的最后到达时刻, value: route信息}
route_time_dict = defaultdict(list)

# 开始程序---------

# 方案1海湾-南桥汽车站-虹桥
# 海湾到南桥, 上师大 - 上海师范大学东门, 可乘坐fx18或fx9, 上师大出发耗时10分钟
case1_Haiwan_Nanqiao_fx18 = Segment('fx18','海湾到南桥')
case1_result_fx18 = case1_Haiwan_Nanqiao_fx18.getConsumeThen(set_time,10)
case1_Haiwan_Nanqiao_fx9 = Segment('fx9','海湾到南桥')
case1_result_fx9 = case1_Haiwan_Nanqiao_fx9.getConsumeThen(set_time,10)
# 南桥到虹桥, 南桥汽车站 - 南桥汽车站, 可乘坐hq5或hq5b, 南桥汽车站本站换乘2分钟
case1_Nanqiao_Hongqiao_hq5_A = Segment('hq5','南桥到虹桥')
case1_result_hq5_A = case1_Nanqiao_Hongqiao_hq5_A.getConsumeThen(case1_result_fx18[1], 2)
case1_Nanqiao_Hongqiao_hq5_B = Segment('hq5','南桥到虹桥')
case1_result_hq5_B = case1_Nanqiao_Hongqiao_hq5_B.getConsumeThen(case1_result_fx9[1], 2)
case1_Nanqiao_Hongqiao_hq5b_A = Segment('hq5b','南桥到虹桥')
case1_result_hq5b_A = case1_Nanqiao_Hongqiao_hq5b_A.getConsumeThen(case1_result_fx18[1], 2)
case1_Nanqiao_Hongqiao_hq5b_B = Segment('hq5b','南桥到虹桥')
case1_result_hq5b_B = case1_Nanqiao_Hongqiao_hq5b_B.getConsumeThen(case1_result_fx9[1], 2)

# 记录路线和对应的Segment类到route_time_dict字典, 方便做最后一步时间对应查找
route_time_dict[(case1_result_hq5_A[1])].append([case1_Haiwan_Nanqiao_fx18,case1_Nanqiao_Hongqiao_hq5_A])
route_time_dict[(case1_result_hq5_B[1])].append([case1_Haiwan_Nanqiao_fx9,case1_Nanqiao_Hongqiao_hq5_B])
route_time_dict[(case1_result_hq5b_A[1])].append([case1_Haiwan_Nanqiao_fx18,case1_Nanqiao_Hongqiao_hq5b_A])
route_time_dict[(case1_result_hq5b_B[1])].append([case1_Haiwan_Nanqiao_fx9,case1_Nanqiao_Hongqiao_hq5b_B])


# 方案2海湾-南桥汽车站-莘庄-虹桥
# 海湾到南桥, 上师大 - 上海师范大学东门, 可乘坐fx18或fx9, 上师大出发耗时10分钟
case2_Haiwan_Nanqiao_fx18 = Segment('fx18','海湾到南桥')
case2_result_fx18 = case2_Haiwan_Nanqiao_fx18.getConsumeThen(set_time,10)
case2_Haiwan_Nanqiao_fx9 = Segment('fx9','海湾到南桥')
case2_result_fx9 = case2_Haiwan_Nanqiao_fx9.getConsumeThen(set_time,10)
# 南桥到莘庄, 南桥汽车站 - 南桥汽车站, 可乘坐xngs, 南桥汽车站本站换乘2分钟
case2_Nanqiao_Xinzhuang_xngs_A = Segment('xngs', '南桥到莘庄')
case2_result_xngs_A = case2_Nanqiao_Xinzhuang_xngs_A.getConsumeThen(case2_result_fx18[1], 2)
case2_Nanqiao_Xinzhuang_xngs_B = Segment('xngs', '南桥到莘庄')
case2_result_xngs_B = case2_Nanqiao_Xinzhuang_xngs_B.getConsumeThen(case2_result_fx9[1], 2)
# 莘庄到虹桥, 莘庄地铁站南广场 - 莘庄地铁站南广场(xhkx, 1min)
case2_Xinzhuang_hongqiao_A = Segment('xhkx', '莘庄到虹桥')
case2_result_xhkx_A = case2_Xinzhuang_hongqiao_A.getConsumeThen(case2_result_xngs_A[1], 1)
case2_Xinzhuang_hongqiao_B = Segment('xhkx', '莘庄到虹桥')
case2_result_xhkx_B = case2_Xinzhuang_hongqiao_B.getConsumeThen(case2_result_xngs_B[1], 1)

route_time_dict[(case2_result_xhkx_A[1])].append([case2_Haiwan_Nanqiao_fx18,case2_Nanqiao_Xinzhuang_xngs_A,case2_Xinzhuang_hongqiao_A])
route_time_dict[(case2_result_xhkx_B[1])].append([case2_Haiwan_Nanqiao_fx9,case2_Nanqiao_Xinzhuang_xngs_B,case2_Xinzhuang_hongqiao_B])


# 方案3海湾-奉贤新城-莘庄-虹桥
# 海湾到奉城, 上师大 - 上海师范大学东门, 可乘坐hs/fx18/fx20, 均为10min
case3_Haiwan_Fengcheng_hs = Segment('hs', '海湾到奉城')
case3_result_hs = case3_Haiwan_Fengcheng_hs.getConsumeThen(set_time,10)
case3_Haiwan_Fengcheng_fx18 = Segment('fx18', '海湾到奉城')
case3_result_fx18 = case3_Haiwan_Fengcheng_fx18.getConsumeThen(set_time,10)
case3_Haiwan_Fengcheng_fx20 = Segment('fx20', '海湾到奉城')
case3_result_fx20 = case3_Haiwan_Fengcheng_fx20.getConsumeThen(set_time,10)
# 奉城到莘庄, 奉城公交站 - 奉城地铁站(hs - m5,3min), 公交南港路站 - 奉城地铁站(fx28/fx20 - m5,6min)
case3_Fengcheng_Xinzhuang_m5_A = Segment('m5', '奉城到莘庄')
case3_result_m5_A = case3_Fengcheng_Xinzhuang_m5_A.getConsumeThen(case3_result_hs[1], 3)
case3_Fengcheng_Xinzhuang_m5_B = Segment('m5', '奉城到莘庄')
case3_result_m5_B = case3_Fengcheng_Xinzhuang_m5_B.getConsumeThen(case3_result_fx18[1], 6)
case3_Fengcheng_Xinzhuang_m5_C = Segment('m5', '奉城到莘庄')
case3_result_m5_C = case3_Fengcheng_Xinzhuang_m5_C.getConsumeThen(case3_result_fx20[1], 6)
# 莘庄到虹桥, 莘庄地铁站 - 莘庄地铁站北广场(xhkxb, 4min)
case3_Xinzhuang_Hongqiao_xhkxb_A = Segment('xhkxb', '莘庄到虹桥')
case3_result_xhkxb_A = case3_Xinzhuang_Hongqiao_xhkxb_A.getConsumeThen(case3_result_m5_A[1], 4)
case3_Xinzhuang_Hongqiao_xhkxb_B = Segment('xhkxb', '莘庄到虹桥')
case3_result_xhkxb_B = case3_Xinzhuang_Hongqiao_xhkxb_B.getConsumeThen(case3_result_m5_B[1], 4)
case3_Xinzhuang_Hongqiao_xhkxb_C = Segment('xhkxb', '莘庄到虹桥')
case3_result_xhkxb_C = case3_Xinzhuang_Hongqiao_xhkxb_C.getConsumeThen(case3_result_m5_C[1], 4)

route_time_dict[(case3_result_xhkxb_A[1])].append([case3_Haiwan_Fengcheng_hs,case3_Fengcheng_Xinzhuang_m5_A,case3_Xinzhuang_Hongqiao_xhkxb_A])
route_time_dict[(case3_result_xhkxb_B[1])].append([case3_Haiwan_Fengcheng_fx18,case3_Fengcheng_Xinzhuang_m5_B,case3_Xinzhuang_Hongqiao_xhkxb_B])
route_time_dict[(case3_result_xhkxb_C[1])].append([case3_Haiwan_Fengcheng_fx20,case3_Fengcheng_Xinzhuang_m5_C,case3_Xinzhuang_Hongqiao_xhkxb_C])


# 方案4海湾-奉贤新城-东川路-虹桥
# 海湾到奉城, 上师大 - 上海师范大学东门, 可乘坐hs/fx18/fx20, 均为10min
case4_Haiwan_Fengcheng_hs = Segment('hs', '海湾到奉城')
case4_result_hs = case4_Haiwan_Fengcheng_hs.getConsumeThen(set_time,10)
case4_Haiwan_Fengcheng_fx18 = Segment('fx18', '海湾到奉城')
case4_result_fx18 = case4_Haiwan_Fengcheng_fx18.getConsumeThen(set_time,10)
case4_Haiwan_Fengcheng_fx20 = Segment('fx20', '海湾到奉城')
case4_result_fx20 = case4_Haiwan_Fengcheng_fx20.getConsumeThen(set_time,10)
# 奉城到东川路, 奉城地铁站(hs - m5,3min), 公交南港路站 - 奉城地铁站(fx28/fx20 - m5,6min)
case4_Fengcheng_Dongchuan_m5_A = Segment('m5', '奉城到东川')
case4_result_m5_A = case4_Fengcheng_Dongchuan_m5_A.getConsumeThen(case4_result_hs[1], 3)
case4_Fengcheng_Dongchuan_m5_B = Segment('m5', '奉城到东川')
case4_result_m5_B = case4_Fengcheng_Dongchuan_m5_B.getConsumeThen(case4_result_fx18[1], 6)
case4_Fengcheng_Dongchuan_m5_C = Segment('m5', '奉城到东川')
case4_result_m5_C = case4_Fengcheng_Dongchuan_m5_C.getConsumeThen(case4_result_fx20[1], 6)
# 东川路到虹桥, 东川路地铁站 - 东川路公交站(mh2, 2min)
case4_Dongchuan_Hongqiao_mh2_A = Segment('mh2', '东川到虹桥')
case4_result_mh2_A = case4_Dongchuan_Hongqiao_mh2_A.getConsumeThen(case4_result_m5_A[1], 2)
case4_Dongchuan_Hongqiao_mh2_B = Segment('mh2', '东川到虹桥')
case4_result_mh2_B = case4_Dongchuan_Hongqiao_mh2_B.getConsumeThen(case4_result_m5_B[1], 2)
case4_Dongchuan_Hongqiao_mh2_C = Segment('mh2', '东川到虹桥')
case4_result_mh2_C = case4_Dongchuan_Hongqiao_mh2_C.getConsumeThen(case4_result_m5_C[1], 2)

route_time_dict[(case4_result_mh2_A[1])].append([case4_Haiwan_Fengcheng_hs,case4_Fengcheng_Dongchuan_m5_A,case4_Dongchuan_Hongqiao_mh2_A])
route_time_dict[(case4_result_mh2_B[1])].append([case4_Haiwan_Fengcheng_fx18,case4_Fengcheng_Dongchuan_m5_B,case4_Dongchuan_Hongqiao_mh2_B])
route_time_dict[(case4_result_mh2_C[1])].append([case4_Haiwan_Fengcheng_fx20,case4_Fengcheng_Dongchuan_m5_C,case4_Dongchuan_Hongqiao_mh2_C])


# 方案5海湾-奉贤新城-颛桥-虹桥
# 海湾到奉城, 上师大 - 上海师范大学东门, 可乘坐hs/fx18/fx20, 均为10min
case5_Haiwan_Fengcheng_hs = Segment('hs', '海湾到奉城')
case5_result_hs = case5_Haiwan_Fengcheng_hs.getConsumeThen(set_time,10)
case5_Haiwan_Fengcheng_fx18 = Segment('fx18', '海湾到奉城')
case5_result_fx18 = case5_Haiwan_Fengcheng_fx18.getConsumeThen(set_time,10)
case5_Haiwan_Fengcheng_fx20 = Segment('fx20', '海湾到奉城')
case5_result_fx20 = case5_Haiwan_Fengcheng_fx20.getConsumeThen(set_time,10)
# 奉贤新城到颛桥, 奉城地铁站(hs - m5,3min), 公交南港路站 - 奉城地铁站(fx28/fx20 - m5,6min)
case5_Fengcheng_Zhuanqiao_m5_A = Segment('m5', '奉城到颛桥')
case5_result_m5_A = case5_Fengcheng_Zhuanqiao_m5_A.getConsumeThen(case5_result_hs[1], 3)
case5_Fengcheng_Zhuanqiao_m5_B = Segment('m5', '奉城到颛桥')
case5_result_m5_B = case5_Fengcheng_Zhuanqiao_m5_B.getConsumeThen(case5_result_fx18[1], 6)
case5_Fengcheng_Zhuanqiao_m5_C = Segment('m5', '奉城到颛桥')
case5_result_m5_C = case5_Fengcheng_Zhuanqiao_m5_C.getConsumeThen(case5_result_fx20[1], 6)
# 颛桥到虹桥, 颛桥地铁站 - 颛桥公交站(mh1, 2min)
case5_Zhuanqiao_Hongqiao_mh1_A = Segment('mh1', '颛桥到虹桥')
case5_result_mh1_A = case5_Zhuanqiao_Hongqiao_mh1_A.getConsumeThen(case5_result_m5_A[1], 2)
case5_Zhuanqiao_Hongqiao_mh1_B = Segment('mh1', '颛桥到虹桥')
case5_result_mh1_B = case5_Zhuanqiao_Hongqiao_mh1_B.getConsumeThen(case5_result_m5_B[1], 2)
case5_Zhuanqiao_Hongqiao_mh1_C = Segment('mh1', '颛桥到虹桥')
case5_result_mh1_C = case5_Zhuanqiao_Hongqiao_mh1_C.getConsumeThen(case5_result_m5_C[1], 2)

route_time_dict[(case5_result_mh1_A[1])].append([case5_Haiwan_Fengcheng_hs,case5_Fengcheng_Zhuanqiao_m5_A,case5_Zhuanqiao_Hongqiao_mh1_A])
route_time_dict[(case5_result_mh1_B[1])].append([case5_Haiwan_Fengcheng_fx18,case5_Fengcheng_Zhuanqiao_m5_B,case5_Zhuanqiao_Hongqiao_mh1_B])
route_time_dict[(case5_result_mh1_C[1])].append([case5_Haiwan_Fengcheng_fx20,case5_Fengcheng_Zhuanqiao_m5_C,case5_Zhuanqiao_Hongqiao_mh1_C])


# 方案6海湾-环城东路-莘庄-虹桥
# 海湾到环东, 上师大 - 华东理工大学(fx29, 15min)
case6_Haiwan_Huandong_fx29 = Segment('fx29', '海湾到环东')
case6_result_fx29 = case6_Haiwan_Huandong_fx29.getConsumeThen(set_time,15)
# 环东到莘庄, 环城东路航南公路公交站 - 环城东路地铁站(m5, 4min)
case6_Huandong_Xinzhuang_m5 = Segment('m5', '环东到莘庄')
case6_result_m5 = case6_Huandong_Xinzhuang_m5.getConsumeThen(case6_result_fx29[1], 4)
# 莘庄到虹桥, 莘庄地铁站 - 莘庄地铁站北广场(xhkxb, 4min)
case6_Xinzhuang_Hongqiao_xhkxb = Segment('xhkxb', '莘庄到虹桥')
case6_result_xhkxb = case6_Xinzhuang_Hongqiao_xhkxb.getConsumeThen(case6_result_m5[1], 4)

route_time_dict[(case6_result_xhkxb[1])].append([case6_Haiwan_Huandong_fx29,case6_Huandong_Xinzhuang_m5,case6_Xinzhuang_Hongqiao_xhkxb])


# 方案7海湾-环城东路-东川路-虹桥
# 海湾到环东, 上师大 - 华东理工大学(fx29, 15min)
case7_Haiwan_Huandong_fx29 = Segment('fx29', '海湾到环东')
case7_result_fx29 = case7_Haiwan_Huandong_fx29.getConsumeThen(set_time,15)
# 环东到东川路, 环城东路航南公路公交站 - 环城东路地铁站(m5, 4min)
case7_Huandong_Dongchuan_m5 = Segment('m5', '环东到东川')
case7_result_m5 = case7_Huandong_Dongchuan_m5.getConsumeThen(case7_result_fx29[1], 4)
# 东川路到虹桥, 东川路地铁站 - 东川路公交站(mh2, 2min)
case7_Dongchuan_Hongqiao_mh2 = Segment('mh2', '东川到虹桥')
case7_result_mh2 = case7_Dongchuan_Hongqiao_mh2.getConsumeThen(case7_result_m5[1], 2)

route_time_dict[(case7_result_mh2[1])].append([case7_Haiwan_Huandong_fx29,case7_Huandong_Dongchuan_m5,case7_Dongchuan_Hongqiao_mh2])


# 方案8海湾-环城东路-颛桥-虹桥
# 海湾到环东, 上师大 - 华东理工大学(fx29, 15min)
case8_Haiwan_Huandong_fx29 = Segment('fx29', '海湾到环东')
case8_result_fx29 = case8_Haiwan_Huandong_fx29.getConsumeThen(set_time,15)
# 环东到颛桥, 环城东路航南公路公交站 - 环城东路地铁站(m5, 4min)
case8_Huandong_Zhuanqiao_m5 = Segment('m5', '环东到颛桥')
case8_result_m5 = case8_Huandong_Zhuanqiao_m5.getConsumeThen(case8_result_fx29[1], 4)
# 颛桥到虹桥, 颛桥地铁站 - 颛桥公交站(mh1, 2min)
case8_Zhuanqiao_Hongqiao_mh1 = Segment('mh1', '颛桥到虹桥')
case8_result_mh1 = case8_Zhuanqiao_Hongqiao_mh1.getConsumeThen(case8_result_m5[1], 2)

route_time_dict[(case8_result_mh1[1])].append([case8_Haiwan_Huandong_fx29,case8_Huandong_Zhuanqiao_m5,case8_Zhuanqiao_Hongqiao_mh1])


#开始展示------------------------
timelistNo = [case1_result_hq5_A[1], case1_result_hq5_B[1], case1_result_hq5b_A[1], case1_result_hq5b_B[1], case2_result_xhkx_A[1], case2_result_xhkx_B[1], case3_result_xhkxb_A[1], case3_result_xhkxb_B[1], case3_result_xhkxb_C[1], case4_result_mh2_A[1], case4_result_mh2_B[1], case4_result_mh2_C[1], case5_result_mh1_A[1], case5_result_mh1_B[1], case5_result_mh1_C[1], case6_result_xhkxb[1], case7_result_mh2[1], case8_result_mh1[1]]
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
print("<h2>设定出发时间为{}:{}, 可快速抵达虹桥枢纽的方案如下:</h2>".format(set_hour,set_min))
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



