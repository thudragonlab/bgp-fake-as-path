import os
import json
from utils import *
import pandas as pd


class ReliableLinkBase:
    def __init__(self) -> None:
        self.reliable_link_set = set()
        self.as_set = set()
        self.mapping = {}
        self.reverse_mapping = {}
        self.trian_data = None
        self.test_data = None
    
    def generate_reliable_link_set(self, date):
        month = 6
        if '-' in str(date):
            print(date)
            no_1 = date[0:8]+'01'
            date = date[0:10].replace('-','')
        else:
            no_1 = date
            date = date
        print(f'获取历史链路集中...{date}')
    

        iter = no_1
        ind = 0
        
        ### Stable AS links
        topo_path = 'data/topo'
        os.makedirs(topo_path,exist_ok=True)
        for i in range(month):
            iter =  get_last_month(iter)
            tmp = iter.replace('-','')
            print(f'获取CAIDA AS relationship数据---{tmp}')
            
            path1 = os.path.join(topo_path,f"{tmp}.as-rel.txt")
            path2 = os.path.join(topo_path,f"{tmp}.as-rel.v6-stable.txt")

            if  not os.path.exists(path1):
                if os.system(f'wget https://publicdata.caida.org/datasets/as-relationships/serial-1/{tmp}.as-rel.txt.bz2 -O {os.path.join(topo_path,f"{tmp}.as-rel.txt.bz2")}') == 0:
                    os.system(f'bzip2 -d {os.path.join(topo_path,f"{tmp}.as-rel.txt.bz2")}')
                    if os.system(f'wget https://publicdata.caida.org/datasets/as-relationships/serial-1/{tmp}.as-rel.v6-stable.txt.bz2  -O {os.path.join(topo_path,f"{tmp}.as-rel.v6-stable.txt.bz2")}') == 0:
                        os.system(f'bzip2 -d {os.path.join(topo_path,f"{tmp}.as-rel.v6-stable.txt.bz2")}' )

            for path in [path1,path2]:
                if os.path.exists(path):
                    with open(path,'r') as fp:
                        for line in fp:
                            if '#' in line:
                                continue
                            u = line.strip().split('|')[0]
                            v = line.strip().split('|')[1]
                            # for a in [u, v]:
                            #     if not a in self.mapping:
                            #         self.mapping[a] = str(ind)
                            #         self.reverse_mapping[str(ind)] = a
                            #         ind += 1
                            self.reliable_link_set.add((u,v))
                            # stable.setdefault(f'{v} {u}',0)
                            # stable[f'{v} {u}'] += 1
                            self.as_set.add(u)
                            self.as_set.add(v)
        
        
    def generate_dataset(self,max_size=300000,date='2022-01-01'):
        month = 6
        if '-' in str(now):
            print(now)
            no_1 = now[0:8]+'01'
            date = now[0:10].replace('-','')
        else:
            no_1 = now
            date = now
        print(f'获取历史链路集中...{now}')
    

        iter = no_1
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
        dataset = []
        ind = 0
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
                            if not a in self.mapping:
                                self.mapping[a] = str(ind)
                                self.reverse_mapping[str(ind)] = a
                                ind += 1
                        dataset.append((u,v))
               
        
        # reliable_link_set转换成dataframe
        mapped_reliable_link_list = [(self.mapping[u],self.mapping[v]) for u,v in dataset]
        
        df = pd.DataFrame(mapped_reliable_link_list,columns=['u','v'])
        
        df = df[:max_size]
        print("所有link:",df.shape)
        df_train = df.sample(frac=0.8,random_state=1)
        # print(df)
        df = df.append(df_train)
        df_test = df.drop_duplicates(keep=False)
        print("训练集link:",df_train.shape)
        # df_test = df - df_train
        print("测试集link:",df_test.shape)  
        return [df_train,df_test]
          

    
    def save_all(self, dir):
        with open(f'{dir}/reliable_link_set.json','w') as fp:
            json.dump(list(self.reliable_link_set),fp)
        with open(f'{dir}/as_set.json','w') as fp:
            json.dump(list(self.as_set),fp)
        with open(f'{dir}/mapping.json','w') as fp:
            json.dump(self.mapping,fp)
        with open(f'{dir}/reverse_mapping.json','w') as fp:
            json.dump(self.reverse_mapping,fp)
       
        
    
    def load_all(self, dir):
        with open(f'{dir}/reliable_link_set.json','r') as fp:
            tmp = json.load(fp)
            self.reliable_link_set = {(i[0],i[1]) for i in tmp}
            # self.reliable_link_set = set(json.load(fp))
        with open(f'{dir}/as_set.json','r') as fp:
            self.as_set = set(json.load(fp))
        with open(f'{dir}/mapping.json','r') as fp:
            self.mapping = json.load(fp)   
        with open(f'{dir}/reverse_mapping.json','r') as fp:
            self.reverse_mapping = json.load(fp)
       
    
    def load_dataset(self,dir):
        train_data = pd.read_csv(f'{dir}/train.txt')
        test_data = pd.read_csv(f'{dir}/test.txt')
        with open(f'{dir}/mapping.json','r') as fp:
            self.mapping = json.load(fp)   
        with open(f'{dir}/reverse_mapping.json','r') as fp:
            self.reverse_mapping = json.load(fp)
        
        return [train_data,test_data]
    def save_dataset(self,train_data,test_data,dir):
        train_data.to_csv(f'{dir}/train.txt',index = False)
        test_data.to_csv(f'{dir}/test.txt',index = False)
        with open(f'{dir}/mapping.json','w') as fp:
            json.dump(self.mapping,fp)
        with open(f'{dir}/reverse_mapping.json','w') as fp:
            json.dump(self.reverse_mapping,fp)

    
    def __contains__(self,item):
        if item in self.reliable_link_set:
            return True
        elif item in self.as_set:
            return True
        return False