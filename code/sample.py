

import random
import json

# print(random.randint(1,9))

with open('data/stable/as_set_20211101.json','r') as f:
    as_list = list(json.load(f).keys())

# 生成编辑距离为1的字符串列表
def edit_distance_1(s):
    res = []
    for i in range(len(s)):
        for j in range(10):
            if s[i] == str(j):
                continue
            else:
                res.append(s[:i] + str(j) + s[i+1:])
    for i in range(len(s)):
        if i == len(s)-1:
            break
        else:
            res.append(s[:i] + s[i+1] + s[i] + s[i+2:])
    return res


def miscofiguration_1(as_path):
            asn = random.randint(1,9)
            as_path = as_path.strip()  +  ' ' + str(asn)
            return as_path

def miscofiguration_2(as_path):
        origin_asn = as_path.strip().split(' ')[-1]
        res = edit_distance_1(origin_asn)
        # 从list中随机sample k个元素
        as_path = as_path.strip()  + ' ' + str(random.sample(res, 1)[0].strip())
        return as_path
            
def get_candidate(k,pools):
     # 对pools中的as_path去掉重复的as
    candidate_as_path = []
    for as_path in pools:
        as_path = as_path.split(' ')
        # 对as_path中的相邻as去重，只保留一个
        as_path_new = []
        last_asn = '-1'
        for asn in as_path:
            if asn != last_asn:
                as_path_new.append(asn)
                last_asn = asn
        
        if len(as_path_new) >= k:
            # print(as_path,as_path_new,as_path_new[-k:])
            
            candidate_as_path.append(' '.join(as_path_new[-k:]))
    return candidate_as_path
def type_k_hijack(as_path,candidates):
    as_path = as_path.strip()  + ' ' + str(random.sample(candidates,1)[0])
    return as_path
    # 从candidate_as_path中随机1个元素

def type_11_hijack(as_path,candidates):
    as_path = as_path.strip()  + ' ' + random.sample(as_list,1)[0]
    return as_path



def bgp_poinsoning_k(as_path,k):
    return as_path.strip() + ' ' + ' '.join(random.sample(as_list,k)) + ' ' + as_path.split(' ')[-1].strip()

    
     

    
# 从文件AS_PATH.txt中随机sample 1000个as-path
def random_path():
    random.seed(1)
    with open('data/simulation/AS_PATH.txt', 'r') as f:
        lines_all = f.readlines()
        lines = random.sample(lines_all, 14000)
        # 从lines_all中删除lines
        lines_all = list(set(lines_all) - set(lines))
        
        with open('data/simulation/true_as_path.txt', 'w') as f2:
            for line in lines:
                f2.write(line)
        print('true_as_path.txt done')
    
        # lines = random.sample(lines_all, 1000)
        # lines_all = list(set(lines_all) - set(lines))
        # with open('data/simulation/misconfiguration_1.txt', 'w') as f2:
        #     for line in lines:
        #         f2.write(miscofiguration_1(line))
        #         f2.write('\n')
        # print('misconfiguration_1.txt done')
        # lines = random.sample(lines_all, 1000)
        # lines_all = list(set(lines_all) - set(lines))
        # with open('data/simulation/misconfiguration_2.txt', 'w') as f2:
        #     for line in lines:
        #         f2.write(miscofiguration_2(line))
        #         f2.write('\n')
        # print('misconfiguration_2.txt done')
        
        
        # for k in range(1,4):
        #     lines = random.sample(lines_all, 1000)
        #     lines_all = list(set(lines_all) - set(lines))
        #     # pools = random.sample(lines_all,2000000)
        #     pools = lines_all
        #     with open(f'data/simulation/type_{k}_hijack.txt', 'w') as f2:
        #         k_candidate = get_candidate(k,pools)
        #         for line in lines:
        #             f2.write(type_k_hijack(line,k_candidate))
        #             f2.write('\n')
        #     print(f'type_{k}_hijack.txt done')
        # exit() 
          
        # lines = random.sample(lines_all, 1000)
        # lines_all = list(set(lines_all) - set(lines))
        # with open('data/simulation/type_11_hijack.txt', 'w') as f2:
        #     for line in lines:
        #         f2.write(type_11_hijack(line,as_list))
        #         f2.write('\n')
        # print('type_11_hijack.txt done')
            
        for k in range(1,3):
            lines = random.sample(lines_all, 1000)
            lines_all = list(set(lines_all) - set(lines))
            with open(f'data/simulation/bgp_poinsoning_{k}.txt', 'w') as f2:
                for line in lines:
                    f2.write(bgp_poinsoning_k(line,k))
                    f2.write('\n')
            print(f'bgp_poinsoning_{k}.txt done')
            
       
        
    
random_path()