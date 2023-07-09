

from utils import *
import os
import sys
# 给定一个时间'20211101',输出当天给定异常的所有链路以及统计结果。

start_date = date(2021, 10, 1)
id = 'amazon_1'

threshold = 1.5



stable_links,as_set,ixp_set,mapping,r_mapping= get_stable_link_dict(id,now = str(start_date))
TRAIN = False
if TRAIN:
    prepare_dataset(id)
    if not os.path.exists(f'SEAL/Python/model/{id}_model.pth'):
        os.system(f'cd SEAL/Python/; python3.8 Main.py  --train-path data/topo/{id}/{id}_train.txt --test-path data/topo/{id}/{id}_test.txt --save-model' )
    
with open('data/irr/20211001_as_dict.json') as fp:
    irr_as_dict = json.load(fp) 
with open('data/ihr_hegemony_ipv4_global_2022-01-01.json', 'r') as fp:
    hegemony_dict = json.load(fp)


filtered_asn = ['7700','18619','41593','53910','1999','13071']
                
     

def detect2(file_path):
    to_pred= []
    filtered_cnt = 0  
    with open(file_path,'r') as fp:
        valid = True
        type_0 = []
        type_1 = []
        type_2 = []
        

        for as_path in fp:
            as_links = as_path2links(as_path)
            # print(as_links)
            for as_link in as_links:
                    # 过滤稳定链路
                    # print(stable_links.keys())
                    if f'{as_link[0]} {as_link[1]}' in stable_links or f'{as_link[1]} {as_link[0]}' in stable_links:
                        type_0.append(as_link)
                        continue
                    if as_link[0] not in as_set or as_link[1] not in as_set:
                        # Type-1 link
                        type_1.append(as_link)
                        if as_link[0] not in as_set:
                            key = 0
                            value = as_link[0]
                        else:
                            key = 1
                            value = as_link[1]
                            
                        if value not in irr_as_dict:
                            valid = False
                        

                    else:
                        # Type-2 link
                       
                        type_2.append(as_link)
                        tmp = (mapping[as_link[0]],mapping[as_link[1]])
                        if tmp[0] in filtered_asn or tmp[1] in filtered_asn:
                            filtered_cnt += 1
                            continue
                        to_pred.append(tmp)
                        
    print(len(set(type_0)),len(set(type_1)),len(set(type_2)),filtered_cnt)
    with open('data/simulation/to_pred.txt','w') as tfp:
        for as_link in to_pred:
            tfp.write(f'{as_link[0]} {as_link[1]}\n')
    # 用模型预测
    print('predicting...')
    os.system(f'python3.8 SEAL/Python/Main.py  --train-path data/topo/{id}/{id}_train.txt --test-path data/simulation/to_pred.txt --pred-path data/simulation/pred_result.txt   --only-predict')
    dt = {}
    with open('data/simulation/pred_result.txt','r') as tfp:
        for line in tfp:
            u,v,w = line.strip().split(' ')
            dt[(u,v)] = float(w)
    # 标记预测结果
    with open(file_path,'r') as fp:
        with open(file_path.replace('.txt','_pred.txt'),'w') as fp2:
           
            for as_path in fp:
                valid = True
                invalid_link = []
                valid_link = []
                as_links = as_path2links(as_path)
                level = -1
                reason = ''
                for as_link in as_links:
                        # 过滤稳定链路
                        
                        if f'{as_link[0]} {as_link[1]}' in stable_links or f'{as_link[1]} {as_link[0]}' in stable_links:
                            type_0.append(as_link)
                            continue
                        if as_link[0] not in as_set or as_link[1] not in as_set:
                            # Type-1 link
                            type_1.append(as_link)
                            if as_link[0] not in as_set:
                                key = 0
                                value = as_link[0]
                            else:
                                key = 1
                                value = as_link[1]
                                
                            if value not in irr_as_dict:
                                valid = False
                                level,reason = 0,'Type-1 invalid link'
                                invalid_link.append(f'{as_link[0]} {as_link[1]},invalid_as {value}')

                        else:
                            # Type-2 link
                            type_2.append(as_link)
                            tmp = (mapping[as_link[0]],mapping[as_link[1]])
                            if (tmp[0],tmp[1]) not in dt:
                                continue
                            w = dt[(tmp[0],tmp[1])]
                            if(dt[(tmp[0],tmp[1])] < threshold):
                                invalid_link.append(f'{as_link[0]} {as_link[1]} {w}')
                                valid = False
                
                                tmp_level,tmp_reason = rank(as_link,w,as_links,irr_as_dict,hegemony_dict)
                                if tmp_level > level:
                                    level = tmp_level
                                    reason = tmp_reason
                            else:
                                valid_link.append(f'{as_link[0]} {as_link[1]} {w}')
                                
                                
                fp2.write(f'{as_path.strip()}\n')
                fp2.write('valid: '+str(valid)+'\n')
                fp2.write(f'valid links:{valid_link}\n')
                fp2.write(f'invalid links:{invalid_link}\n')
                fp2.write(f'level:{level} reason:{reason}\n')
                fp2.write('\n')
            
                


if len(sys.argv) == 2:             
    detect2(sys.argv[1]) 
# detect('data/simulation/bgp_poinsoning_1_.txt')
# detect('data/simulation/bgp_poinsoning_2_.txt')


# paths = [
#     'data/simulation/bgp_poinsoning_1_.txt',
#     'data/simulation/bgp_poinsoning_2_.txt',
#     'data/simulation/type_11_hijack.txt',
#     'data/simulation/type_2_hijack_.txt',
#     'data/simulation/type_3_hijack_.txt',
#     'data/simulation/misconfiguration1_.txt',
#     'data/simulation/misconfiguration2_.txt',
# ]
# detect2('data/simulation/type_11_hijack.txt') 


detect2('data/simulation/true_as_path.txt')
# for path in paths:
#     detect2(path)
    
               
               
            
            
      
        
