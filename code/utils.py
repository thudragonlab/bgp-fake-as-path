from email import headerregistry
import json
import collections
import datetime
import os
import pandas as pd
from typing import DefaultDict
import pybgpstream
import time
import pdb
from datetime import date, timedelta
import requests
from lxml import html 
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
import glo
glo._init()

# 1.定义发送邮件
def send_email(email_addr, send_msg, send_subject):
    """
    
    :param email_addr: 收件人邮件地址
    :param send_msg: 发送的消息
    :param send_subject: 发送的标题/主题
    :return: 
    """
    # 1.右键内容配置
    msg = MIMEText(send_msg, "html", "utf-8")
    msg['From'] = formataddr(["Chengwan Zhang", "zhangcw20@mails.tsinghua.edu.cn"])
    msg["Subject"] = send_subject

    # 2.发送邮件
    server = smtplib.SMTP_SSL('mails.tsinghua.edu.cn')
    server.login("zhangcw20@mails.tsinghua.edu.cn", "qwer100084")
    server.sendmail("zhangcw20@mails.tsinghua.edu.cn", email_addr, msg.as_string())
    server.quit()
    print("发送邮件成功")


def get_latest_update_online(project='ripe',collector="rrc00"):
    url = 'https://data.ris.ripe.net/rrc00/' 
    try:
        r = requests.get(url).content 
    except:
        pass
    # time_ = html.fromstring(r).xpath("/html/body/table/tr[5]/td[3]/text()") 
    
    time_ = html.fromstring(r).xpath("/html/body/pre/text()[286]") 
    print(time_)
    # /html/body/pre/a[3]

    glo.set_global_var('Last_modified',time_[0])
    
    rib_url = fr'https://data.ris.ripe.net/{collector}/latest-update.gz'
    os.system(fr'curl --connect-timeout 60 -m 300 {rib_url} --output  /home/pzd/bgp-fake-as-path/tmp/{collector}_latest-update.gz')
    os.system(fr'bgpdump -m /home/pzd/bgp-fake-as-path/tmp/{collector}_latest-update.gz > /home/pzd/bgp-fake-as-path/tmp/{collector}_latest-update.txt')
    
    return f'/home/pzd/bgp-fake-as-path/tmp/{collector}_latest-update.txt'

def check_if_new_latest_update():
    last_modified = glo.get_global_var('Last_modified')
    url = 'https://data.ris.ripe.net/rrc00/'
    continue_ = 1 
    while continue_:
        try:
            r = requests.get(url).content 
            continue_ = 0
        except :
            continue_ = 1
        
    # time_ = html.fromstring(r).xpath("/html/body/table/tr[5]/td[3]/text()") 
    time_ = html.fromstring(r).xpath("/html/body/pre/a[@href='latest-update.gz']/following-sibling::text()") 
    time_ = time_[0].strip().split('      ')[0]
    this_last_modified = time_
    print(f'{last_modified} and {this_last_modified}')
    return last_modified != this_last_modified

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

now = '2021-11-01 00:00:00'


def timestamp2date(timestamp):
    return datetime.datetime.utcfromtimestamp(float(timestamp)).strftime(
                    "%Y-%m-%d %H:%M:%S")

def date2timestamp(date):
    timeArray = time.strptime(date, "%Y-%m-%d %H:%M:%S")
    timestamp = int(time.mktime(timeArray))
    return timestamp

def prepare_dataset(id):
    print('数据集准备...')
    max_size = 400000
    df = pd.read_csv(f'data/topo/{id}/{id}_mapped_links.txt',sep = ' ',header=None,names=['u','v'])
    df = df[:max_size]
    print("所有link:",df.shape)
    df_train = df.sample(frac=0.8,random_state=1)
    # print(df)
    df = df.append(df_train)
    df_test = df.drop_duplicates(keep=False)
    
    df_train.to_csv(f'data/topo/{id}/{id}_train.txt',sep = ' ',header=None,index=False)
    df_test.to_csv(f'data/topo/{id}/{id}_test.txt',sep = ' ',header=None,index=False)
    print("训练集link:",df_train.shape)
    # df_test = df - df_train
    print("测试集link:",df_test.shape)

def get_last_month(now):
    now = now.replace('-','')
    # print(now)
    now = datetime.date(int(now[0:4]),int(now[4:6]),int(now[6:8]))
    last_day_of_prev_month = now.replace(day=1) - datetime.timedelta(days=1)
    start_day_of_prev_month = now.replace(day=1) - datetime.timedelta(days=last_day_of_prev_month.day)
    return str(start_day_of_prev_month)

def get_next_month(now):
    now = now.replace('-','')
    # print(now)
    now = datetime.date(int(now[0:4]),int(now[4:6]),int(now[6:8]))
    last_day_of_prev_month = now.replace(day=1) + datetime.timedelta(days=32)
    last_day_of_prev_month = last_day_of_prev_month.replace(day=1)
    return str(last_day_of_prev_month)

def get_stable_link_dict(id,now,month=6):
    # now = '2021-11-01 00:00:00'
    if '-' in str(now):
        print(now)
        no_1 = now[0:8]+'01'
        date = now[0:10].replace('-','')
    else:
        no_1 = now
        date = now
    print(f'获取历史链路集中...{now}')
    
    cache_mode = False
    if os.path.exists(f'data/stable/stable_{id}.json') and cache_mode:
        print(id)
        with open(f'data/stable/stable_{id}.json','r') as fp:
            stable = json.load(fp)
        with open(f'data/stable/as_set_{id}.json','r') as fp:
            as_set = json.load(fp)
        with open(f'data/stable/ixp_list_{id}.json','r') as fp:
            ixp_set = json.load(fp)
        with open(f'data/topo/{id}/{id}.json','r') as fp:
            mapping = json.load(fp)
        r_mapping = {v:k for k,v in mapping.items()}
        return stable,as_set,ixp_set,mapping,r_mapping

    iter = no_1
    stable = {}
    as_set = {}
    ixp_set = {}
    mapping = {}
    dataset = {}
    ind = 0
    
    ### Stable AS links
    for i in range(month):
        iter =  get_last_month(iter)
        tmp = iter.replace('-','')
        print(f'获取CAIDA AS relationship数据---{tmp}')
        
        path1 = f'data/topo/{tmp}.as-rel.txt'
        path2 = f'data/topo/{tmp}.as-rel.v6-stable.txt'

        if  not os.path.exists(f'data/topo/{tmp}.as-rel.txt'):
            if os.system(f'wget https://publicdata.caida.org/datasets/as-relationships/serial-1/{tmp}.as-rel.txt.bz2 -O data/topo/{tmp}.as-rel.txt.bz2') == 0:
                os.system(f'bzip2 -d data/topo/{tmp}.as-rel.txt.bz2 ')
                if os.system(f'wget https://publicdata.caida.org/datasets/as-relationships/serial-1/{tmp}.as-rel.v6-stable.txt.bz2  -O data/topo/{tmp}.as-rel.v6-stable.txt.bz2') == 0:
                    os.system(f'bzip2 -d data/topo/{tmp}.as-rel.v6-stable.txt.bz2' )

        for path in [path1,path2]:
            # print('.')
            if os.path.exists(path):
                with open(path,'r') as fp:
                    for line in fp:
                        if 'IXP' in line:
                            ixp_list = line.strip().split(' ')[3:]
                            for ixp in ixp_list:
                                ixp_set.setdefault(ixp,0)
                                ixp_set[ixp] += 1
                        if '#' in line:
                            continue
                        u = line.strip().split('|')[0]
                        v = line.strip().split('|')[1]
                        for a in [u, v]:
                            if not a in mapping:
                                mapping[a] = str(ind)
                                ind += 1
                        stable.setdefault(f'{u} {v}',0)
                        # stable.setdefault(f'{v} {u}',0)
                        stable[f'{u} {v}'] += 1
                        # stable[f'{v} {u}'] += 1
                        as_set.setdefault(u,0)
                        as_set.setdefault(v,0)
                        as_set[u] += 1
                        as_set[v] += 1
    
    
    
    ### Dataset
    iter = no_1
    for i in range(1):
        iter =  get_last_month(iter)
        tmp = iter.replace('-','')
        print(f'获取数据集数据...{tmp}')
        
        path1 = f'data/topo/{tmp}.as-rel.txt'
        path2 = f'data/topo/{tmp}.as-rel.v6-stable.txt'

        if  not os.path.exists(f'data/topo/{tmp}.as-rel.txt'):
            if os.system(f'wget https://publicdata.caida.org/datasets/as-relationships/serial-1/{tmp}.as-rel.txt.bz2 -O data/topo/{tmp}.as-rel.txt.bz2') == 0:
                os.system(f'bzip2 -d data/topo/{tmp}.as-rel.txt.bz2 ')
                if os.system(f'wget https://publicdata.caida.org/datasets/as-relationships/serial-1/{tmp}.as-rel.v6-stable.txt.bz2  -O data/topo/{tmp}.as-rel.v6-stable.txt.bz2') == 0:
                    os.system(f'bzip2 -d data/topo/{tmp}.as-rel.v6-stable.txt.bz2' )

        for path in [path1,path2]:
            # print('.')
            if os.path.exists(path):
                with open(path,'r') as fp:
                    for line in fp:
                        if '#' in line:
                            continue
                        u = line.strip().split('|')[0]
                        v = line.strip().split('|')[1]
                        for a in [u, v]:
                            if not a in mapping:
                                mapping[a] = str(ind)
                                ind += 1
                        dataset.setdefault(f'{u} {v}',0)
                        # stable.setdefault(f'{v} {u}',0)
                        dataset[f'{u} {v}'] += 1
                        # stable[f'{v} {u}'] += 1

    
    if not os.path.exists(f'data/topo/{id}/{id}_mapped_links.txt'):
        os.system(f'mkdir data/topo/{id}/')
    with open(f'data/topo/{id}/{id}_mapped_links.txt','w') as fp:
        for link in dataset.keys():
            u,v = link.strip().split(' ')[0],link.strip().split(' ')[1]
            fp.write(f'{mapping[u]} {mapping[v]}\n')
    # list = list(stable.keys())
    # for link in list:
    #     u,v = link.split(' ')[0],link.split(' ')[1]
    #     stable.setdefault(f'{v} {u}',0)
    #     stable[f'{v} {u}'] += 1

    



    with open(f'data/stable/stable_{id}.json','w') as fp:
        json.dump(stable,fp)
    with open(f'data/stable/as_set_{id}.json','w') as fp:
        json.dump(as_set,fp)
    with open(f'data/stable/ixp_list_{id}.json','w') as fp:
        json.dump(ixp_list,fp)
    with open(f'data/topo/{id}/{id}.json','w') as fp:
        json.dump(mapping,fp)

    #获取mapping的反向字典，id->as
    r_mapping = {}
    for key in mapping.keys():
        r_mapping[mapping[key]] = key
    print("stable:",len(stable))
    print("as set:",len(as_set))
    print("ixp set:",len(ixp_set))

    return stable,as_set,ixp_set,mapping,r_mapping
        
date_list = [
            '19980101',
            '19990201',
            '20000101',
            '20010101',
            '20020101',
            '20030101',
            '20040101',
            '20050101',
            '20060101',
            '20070101',
            '20080101',
            '20090101',
            '20100101',
            '20110101',
            '20120101',
            '20130101',
            '20140401',
            '20150101',
            '20160101',
            '20170101',
            '20180101',
            '20190101',
            '20200101',
            '20210101',
            '20220101',
]

def get_route(id,start_date,end_date,stable_link_dict,as_set,ixp_list,mapping,filter='type updates'):
    print('获取路由中...')
    if os.path.exists(f'data/result/{id}/updates'):
        print('已经获取过路由了')
        return 
    # now = start_time.replace('-','')
    path_num = 0
    all= 0
    normal = 0
    type1 = 0
    type2 = 0
    new_as_set = set()
    all_link = set()
    normal_link = set()
    type1_link = set()
    type2_link = set()
    if not os.path.exists(f'data/result/{id}'):
        os.system(f'mkdir data/result/{id}')
    if not os.path.exists(f'data/topo/{id}'):
        os.system(f'mkdir data/topo/{id}')
    
    #     filter = 'type updates'
    # else:
    #     filter = filter
    # fp0 = open('fdata/result/{id}/{id}','w')
    
    fp00 = open(f'data/result/{id}/updates','w')
    fp11 = open(f'data/result/{id}/type1_route.txt','w')
    fp22 = open(f'data/result/{id}/type2_route.txt','w')
    fp33 = open(f'data/topo/{id}/type2.link','w')# 待预测的压缩后的link
    fp44 = open(f'data/result/{id}/new_as.txt','w')
    fp55 = open(f'data/result/{id}/type1_link.txt','w')
    fp66 = open(f'data/result/{id}/type2_link.txt','w') 
    fp77 = open(f'data/result/{id}/type0_link.txt','w')


   
    # cache_mode = True
    cache_mode = False

    
    for single_date in daterange(start_date, end_date):
        s_ = time.time()
        
        start_time = single_date.strftime("%Y-%m-%d") + ' 00:00:00'
        until_time = str(single_date + datetime.timedelta(days=1)) + ' 00:00:00'
        print(start_time,until_time)
        # fp0 = open(f'data/result/{id}/{single_date}_updates','w')
        # fp1 = open(f'data/result/{id}/{single_date}_type1_route.txt','w')
        # fp2 = open(f'data/result/{id}/{single_date}_type2_route.txt','w')
        # fp3 = open(f'data/topo/{id}/{single_date}_type2.link','w')# 待预测的压缩后的link
        # fp4 = open(f'data/result/{id}/{single_date}_new_as.txt','w')
        # fp5 = open(f'data/result/{id}/{single_date}_type1_link.txt','w')
        # fp6 = open(f'data/result/{id}/{single_date}_type2_link.txt','w')
        fp7 = open(f'data/result/{id}/{single_date}_type0_link.txt','w')
        all_cur= 0
        normal_cur = 0
        type1_cur = 0
        type2_cur = 0
        new_as_set_cur = set()
        all_link_cur = set()
        normal_link_cur = set()
        type1_link_cur = set()
        type2_link_cur = set()   
        def count(as_path):
            nonlocal all,normal,type1,type2, all_cur,normal_cur,type1_cur,type2_cur
            # print(as_path)
            
            o_as_path = as_path
            as_path = as_path.strip().split(' ')
            # i = 0
            # while i < len(as_path):
                
            #     if as_path[i] in ixp_list:
            #         as_path.pop(i)
            #     else:
            #         i += 1
            
            for i in range(len(as_path)-1):
                u,v = as_path[i],as_path[i+1]
                # print(u,v)
                # if u in ixp_list:  
                #     print(u,v)
                if u==v:
                    continue # 去环路
                all += 1
                all_cur += 1
                all_link.add((u,v))
                all_link_cur.add((u,v))
                if f'{u} {v}' in stable_link_dict or f'{v} {u}' in stable_link_dict:
                    normal += 1
                    normal_cur += 1
                    normal_link.add((u,v))
                    normal_link_cur.add((u,v))
                    
                elif u not in as_set or v not in as_set:
                    type1 += 1
                    type1_cur += 1
                    type1_link.add((u,v))
                    type1_link_cur.add((u,v))
                    if u not in as_set:
                        new_as_set.add(u)
                        new_as_set_cur.add(u)
                        # fp1.write(f'{timestamp2date(time_)}|{prefix}|{o_as_path}|{u} {v}|{u}\n')
                        fp11.write(f'{timestamp2date(time_)}|{prefix}|{o_as_path}|{u} {v}|{u}\n')
                    else:
                        new_as_set.add(v)
                        new_as_set_cur.add(v)
                        # fp1.write(f'{timestamp2date(time_)}|{prefix}|{o_as_path}|{u} {v}|{v}\n')
                        fp11.write(f'{timestamp2date(time_)}|{prefix}|{o_as_path}|{u} {v}|{v}\n')
                else:
                    type2 += 1
                    type2_cur += 1
                    type2_link.add((u,v))
                    type2_link_cur.add((u,v))
                    # fp2.write(f'{timestamp2date(time_)}|{prefix}|{o_as_path}|{u} {v}\n')
                    fp22.write(f'{timestamp2date(time_)}|{prefix}|{o_as_path}|{u} {v}\n')
        
        if os.path.exists(f'data/result/{id}/{single_date}_updates') and cache_mode and os.stat(f'data/result/{id}_updates').st_size>1000:
            print('使用缓存...')
            with open(f'data/result/{id}/{single_date}_updates') as fp:
                for elem in fp:
                    elem = elem.split('|')
                    time_,prefix,as_path = elem[2],elem[9],elem[11]

                    count(as_path)
        else:  
            # pass
            # begin_time = start_time
            # until_time = end_time
            record_type="updates"
            # start_date = 
            # end_date = date(2021, 12, 1)
            # until_time = start_date.strftime("%Y-%m-%d") + ' 00:00:00'
            # exit() 
            print('使用CAIDA API下载路由中...')
            stream = pybgpstream.BGPStream(
                            # Consider this time interval:
                            # Sat, 01 Aug 2015 7:50:00 GMT -  08:10:00 GMT
                            from_time=start_time, until_time=until_time,
                            collectors=["rrc00",
                                        # 'rrc01',
                                        # 'rrc02',
                                        # 'rrc03',
                                        # 'rrc04',
                                        # 'rrc05',
                                        # 'rrc06',
                                        # 'rrc07',
                                        # 'rrc08',
                                        # 'rrc09',
                                        # 'rrc10',
                                        # 'rrc11',
                                        # 'rrc12',
                                        # 'rrc13',
                                        # 'rrc14',
                                        # 'rrc15',
                                        # 'rrc16',
                                        # 'rrc18',
                                        # 'rrc19',
                                        # 'rrc20',
                                        # 'rrc21',
                                        # 'rrc22',
                                        # 'rrc23',
                                        ],
                            record_type=record_type,  # announcement、rib field中才有as-path，
                            # withdrawal中只有prefix
                            # filter=f'prefix more {event["prefix"]} '
                            # filter =  filter
                            # https://github.com/CAIDA/libbgpstream/blob/master/FILTERING
                            # filter='ipversion 4 and path "_{:}$"'.format(VICTIM_AS),
                        ) 
            
            for rec in stream.records():
                for elem in rec:
                    # fp0.write(f'{str(elem)}\n')
                    fp00.write(f'{str(elem)}\n')
                    # fp0.write(f'{timestamp2date(time_)}|{prefix}|{as_path}\n')
                    if elem.type != 'A':
                        continue
                        
                    time_,prefix,as_path = elem.time,elem._maybe_field('prefix'),elem._maybe_field('as-path')
                    if '{' in as_path:
                        continue
                    # print(time_,prefix,as_path)
                    # print(as_path)
                    count(as_path)
          
            print(f'所有link数目({single_date}):',len(all_link_cur))
            print(f'正常link数目({single_date}):',len(normal_link_cur))
            print(f'Type1 link数({single_date}):',len(type1_link_cur))
            print(f'Type2 link数({single_date}):',len(type2_link_cur))
            print(f'新AS数({single_date})：',len(new_as_set_cur))
                
        for link in list(type1_link):
            # fp5.write(f'{link[0]} {link[1]}\n')
            fp55.write(f'{link[0]} {link[1]}\n')
            pass
        for link in list(type2_link):
            # print(link[0],link[1])
            # fp6.write(f'{link[0]} {link[1]}\n')
            fp66.write(f'{link[0]} {link[1]}\n')
            # fp3.write(f'{mapping[link[0]]} {mapping[link[1]]}\n')
            fp33.write(f'{mapping[link[0]]} {mapping[link[1]]}\n')
            pass
        for link in list(normal_link_cur):
            fp7.write(f'{link[0]} {link[1]}\n')
            fp77.write(f'{link[0]} {link[1]}\n')
        for asn in new_as_set:
            # fp4.write(asn)
            fp44.write(asn)
            # fp4.write('\n')
            fp44.write('\n')
            pass
        e_ = time.time()
        print(f'{e_-s_}')
        # fp0.close()
        # fp1.close()			
        # fp2.close()
        # fp3.close()
        # fp4.close()
        # fp5.close()
        # fp6.close()
        fp7.close()
    print('所有link数目:',len(all_link))
    print('正常link数目:',len(normal_link))
    print('Type1 link数:',len(type1_link))
    print('Type2 link数:',len(type2_link))
    print('新AS数：',len(new_as_set))
    
    fp00.close()
    fp11.close()			
    fp22.close()
    fp33.close()
    fp44.close()
    fp55.close()
    fp66.close()
    fp77.close()

    
        
    
    # os.system(r'awk -F'|' '{OFS = "|"; print $2,$3,$4}'  data/result/{id}/{id}type1_route.txt |sort |uniq -c > data/result/{id}/{id}type1_route_uniq.txt')
    print(f'待预测链路保存到：data/topo/{id}_type2.link')
    print(f'缓存updates保存到：data/result/{id}_updates')


    return type2_link
    
def get_pred(path,threshold=0.3):
    pred_dict = {}
    all = 0
    ok = 0
    with open(path,'r') as fp:
        for line in fp:
            all += 1
            u,v,w = line.strip().split(' ')
            pred_dict[(u,v)] = w
            if float(w) > threshold:
                ok+=1
    if all == 0:
        print('no type2 link')
    else:
        print('正常比例',ok,all,ok/all)
    return pred_dict

def mark_route(id,stable_link_dict,as_set,ixp_list,mapping,pred_dict,threshold):
    print('标记中...')
    suspicious_link_set = set()
    fp0 = open(f'data/result/{id}/suspicious_link.txt','w')
    fp1 = open(f'data/result/{id}/suspicious_route.txt','w')
    fp2 = open(f'data/result/{id}/all_route.txt','w')
    fp3 = open(f'data/result/{id}/type2_pred.txt','w')
    with open(f'data/result/{id}/type2_route.txt','r') as fp:
        for line in fp:
            # print(line)
            line = line.strip().split('|')
            time_,prefix,as_path,link = line[0],line[1],line[2],line[3]
            
            as_path = as_path.strip().split(' ')
            o_as_path = as_path
            i = 0
            while i < len(as_path):
                if as_path[i] in ixp_list:
                    as_path.pop(i)
                else:
                    i += 1
            for i in range(len(as_path)-1):
                u,v = as_path[i],as_path[i+1]
                # print(u,v)
                if u in ixp_list:
                    print(u,v)
                if u==v:
                    continue
                
                if f'{u} {v}' in stable_link_dict or f'{v} {u}' in stable_link_dict:
                    continue
                elif u not in as_set or v not in as_set:
                    continue
                w = -1
                # try:
                
                if (mapping[u],mapping[v]) in pred_dict.keys():
                    w = pred_dict[(mapping[u],mapping[v])]
                if (mapping[v],mapping[u]) in pred_dict:
                    w = pred_dict[(mapping[v],mapping[u])]
                # except:
                #     pass
                fp2.write(f'{time_}|{prefix}|{o_as_path}|{u} {v} {w}\n')
                
                # pdb.set_trace()
                # print(u,v,w)
                if float(w)< threshold:
                    suspicious_link_set.add((u,v,w))
                    # print(w)
                    fp1.write(f'{time_}|{prefix}|{o_as_path}|{u} {v} {w}\n') 

    with open(f'data/result/{id}/type2_link.txt') as fp:
        for line in fp:
            if len(line) < 3:
                break
            u = line.strip().split(' ')[0]
            v = line.strip().split(' ')[1]
            if (mapping[u],mapping[v]) in pred_dict.keys():
                w = pred_dict[(mapping[u],mapping[v])]
            if (mapping[v],mapping[u]) in pred_dict:
                w = pred_dict[(mapping[v],mapping[u])]
            fp3.write(f'{u} {v} {w}\n')
        
    for link in list(suspicious_link_set):
        u,v,w = link[0],link[1],link[2]
        fp0.write(f'{u} {v} {w}\n')
    fp0.close()
    fp1.close()
    fp2.close()
    fp3.close()

    print(f'保存成功(所有type2）：data/result/{id}/all_route.txt')
    print(f'保存成功(可疑type2)：data/result/{id}/suspicious_link.txt')
    # os.system('cd /data/zcw/data/result ; sort type2-.txt  | uniq > type2--.txt')

def suspicious_route_ed():
    pass

def suspicious_route_loop():
    pass

def predicting(id,start_date,end_date):
    for single_date in daterange(start_date, end_date):
        print(single_date)
        os.system(f'cd /home/zhangcw07/paper/fireye+/zcw+/SEAL/Python; python3.8 Main.py --data-name exp  --train-path data/topo/exp/exp_train.txt   --test-path data/topo/exp/{single_date}_delta_type2_link.txt  --pred-path data/topo/exp/{single_date}_delta_type2.pred --only-predict')
        r_mapping = {}
        with open(f'data/topo/{id}/{id}.json','r') as fp:
            mapping = json.load(fp) 
            for key in mapping.keys():
                r_mapping[mapping[key]] = key
        with open(f'data/topo/{id}/{single_date}_delta_type2.pred','r') as fp:
            with open(f'data/result/{id}/{single_date}_delta_type2.pred','w') as fp_:
                for line in fp:
                    u,v,w = line.strip().split(' ')
                    fp_.write(f'{r_mapping[u]} {r_mapping[v]} {w}\n')
        
def as_path2links(as_path):
    link_list = []
    as_path = as_path.strip().split(' ')
    for i in range(len(as_path)-1):
        u,v = as_path[i],as_path[i+1]
        if u != v:
            if '{' in u:
                u = u[1:-1]
            if '{' in v:
                v = v[1:-1]
            if ',' in u or ',' in v:
                continue
            link_list.append((u,v))
    return link_list          
            
def loop(as_link,as_path):
    tmp = {}
    have_loop = False
    start,end = 0,0
    for i,asn in enumerate(as_path):
        if asn in tmp.keys():
            start,end = tmp[asn],i
            break
        else:
            tmp[asn] = i
   
    if as_link[0] in as_path[start:end+1] and as_link[1] in as_path[start:end+1]:
        return True
    return False

def location(as_link,as_links):
    idx = as_links.index(as_link)
    return len(as_links)-1-idx

def valley(as_path,hegemony):
    threshold = 0.95
    
    for i in range(1,len(as_path)-1):
        a,b,c = as_path[i-1],as_path[i],as_path[i+1]
        if a in hegemony.keys() and b in hegemony.keys() and c in hegemony.keys():
            h_a,h_b,h_c = float(hegemony[a]),float(hegemony[b]),float(hegemony[c])
            if h_a > h_b and h_b < h_c:
                deep = ((h_a - h_b)/h_a + (h_c - h_b)/h_c)/2
                if  deep> 1:
                    # print(a,b,c,deep)
                    return (a,b,c),True
    return None,False
  
# 计算两个字符串的编辑距离           
def damerau_levenshtein_distance(string1, string2):
    m = len(string1)
    n = len(string2)
    d = [[0] * (n + 1) for _ in range(m + 1)]
    # 初始化第 1 列
    for i in range(m + 1):
        d[i][0] = i
    # 初始化第 1 行
    for j in range(n + 1):
        d[0][j] = j
    # 自底向上递推计算每个 d[i][j] 的值
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if string1[i - 1] == string2[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = min(d[i - 1][j], d[i][j - 1], d[i - 1][j - 1]) + 1
            if i > 1 and j > 1 and string1[i - 1] == string2[j - 2] and string1[i - 2] == string2[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[m][n]
        
def country_not_continuous(irr_as_dict,as_path):
    visited_countrys = {}
    last_country = irr_as_dict.get(as_path[-1],None)
    for asn in as_path[::-1]:
        if asn not in irr_as_dict.keys():
            continue
        tmp_country = irr_as_dict[asn]['country']
        if tmp_country != None and tmp_country != last_country:
            if tmp_country in visited_countrys.keys():
                return True,tmp_country,[visited_countrys[tmp_country],asn]
            visited_countrys[tmp_country] = asn
            last_country = tmp_country
    return False,None,[]

def rank(as_link,w,as_links,as_dict,hegemony_dict):
    level = 0
    reason = ''
    length_threshold = 9
    as_path = []
    for i in range(len(as_links)):
        as_path.append(as_links[i][0])
    as_path.append(as_links[-1][1])
    # print(as_path)
    if len(set(as_path)) >= length_threshold:
        level = 3
        reason += f'AS-PATH length >= {length_threshold};'
    if loop(as_link,as_path):
        level = 3
        reason += 'AS link in Loop;'
    valley_tuple,flag = valley(as_path,hegemony_dict)
    if flag:
        level = 3
        reason += f'AS-PATH have Valley:{valley_tuple};'
    if int(as_link[1]) < 10 and as_link == as_links[-1]:
        level = 3
        reason += 'AS-PATH end with AS < 10;'
    if damerau_levenshtein_distance(as_link[0],as_link[1]) <= 1:
        level = 3
        reason += 'AS-PATH edit_distance <= 1;'
    # print(as_dict)
    flag,country,ases = country_not_continuous(as_dict,as_path)
    if flag:
        level = 3
        reason += f'{country} in AS-PATH not continuous :{" ".join(ases)};'
        
    if level == 0:
        if as_link[0] in as_dict.keys() and as_link[1] in as_dict.keys():
            if location(as_link,as_links) == 0 and as_dict[as_link[0]].get('country',0) == as_dict[as_link[1]].get('country',1):
                level = 1
                reason = 'Location = 0 & same country'
    if level == 0 :
        level = 2
        reason = 'medium suspicious'
    return level,reason

if __name__ == '__main__':
    # get_stable_link_dict(now)
    predicting('exp',date(2021, 11, 1),date(2021, 12, 1))

    
