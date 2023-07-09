
from Predictor import *
from ReliableLinkBase import *
from RuleEngine import *
from  PathEventManager import *
import os 
## parameters


prediction_threshold = 0.5
AS_PATH_len_threshold = 10
class Fireye:
    def __init__(self):
        self.reliable_links = ReliableLinkBase()
        self.predictor = Predictor()
        self.rule_engine = RuleEngine()
        self.event_manager = PathEventManager()
    
    def prepare_reliable_links(self,dir='data/result/exp2',date=None):
        if dir and os.path.exists(f'{dir}/reliable_link_set.json') :
            print('load reliable_links from file')
            self.reliable_links.load_all(dir)
        else:
            # 获取当前日期
            now = datetime.datetime.now() 
            now = str(now).split(' ')[0]
            print(now)
            self.reliable_links.generate_reliable_link_set(date = date )
            self.reliable_links.generate_dataset(date = date)
            self.reliable_links.save_all(dir)
     
    def prepare_dataset(self,dir='data/result/exp2',date=None):
        if dir and os.path.exists(f'{dir}/train.txt') :
            print('load dataset from file')
            [train_data,test_data] = self.reliable_links.load_dataset(dir)
            return train_data,test_data
        else:
            # 获取当前日期
            # now = datetime.datetime.now() 
            # now = str(now).split(' ')[0]
            # print(now)
            [train_data,test_data] = self.reliable_links.generate_dataset(date) 
            self.reliable_links.save_dataset(train_data,test_data,dir)

            return train_data,test_data
        
    def detect(self,path):
        routes = []
        with open(path, 'r') as fp:
            for line in fp:
                routes.append(line.strip())
        type0_links = set()
        type1_links = set()
        new_ases = set()
        type2_links = set()
        type2_other = set()
        
        # print(len(self.reliable_links.as_set))
        # print(self.reliable_links.as_set)
        # links = {}
        ## 第一遍循环，提取type0和type1的链路
        cnt = 0
        for route in routes:
            # print(route)
            fileds = route.split('|') 
            # timestamp = fileds[1]
            # type = fileds[2]
            # if type != 'A':
            #     continue
            # peer_address,peer_asn,prefix,as_path,next_hop,community = fileds[3],fileds[4],fileds[5].strip(),fileds[6],fileds[8],fileds[11]
            datetime,prefix,as_path = fileds[0],fileds[1],fileds[2]
            ASes = as_path.split(' ')
            # print(as_path)
            for i in range(len(ASes)-1): 
                # 将u中的{和}去除
             
        
                u,v = ASes[i],ASes[i+1]
                if ',' in u or ',' in v:
                    continue
                u = u.replace('{',"").replace('}',"")
                v = v.replace('{',"").replace('}',"")
                u,v = min(int(u),int(v)),max(int(u),int(v)) 
                if u == v:
                    continue
                u,v = str(u),str(v)
                x,y = u in self.reliable_links.as_set,v in self.reliable_links.as_set
                
           
                if x and y:
                    if (u,v) in self.reliable_links or (v,u) in self.reliable_links:
                        type0_links.add((u,v))
                    else:
                        if u not in self.reliable_links.mapping or v not in self.reliable_links.mapping:
                            type2_other.add((u,v))
                            continue
                        type2_links.add((u,v))
                    # links[(u,v)] = [0]
                else:
                    if u not in self.reliable_links.as_set:
                        new_ases.add(u)
                    if v not in self.reliable_links.as_set:
                        new_ases.add(v)
                    # print((u,v))
                    type1_links.add((u,v))


        print(len(new_ases),len(type0_links),len(type1_links),len(type2_links),len(type2_other))
        if len(type1_links) == 0 and len(type2_links) == 0:
            print('No Type-1 links and Type-2 links')
            return
        
            
        type2_links_df = pd.DataFrame(type2_links,columns=['u','v'])
        print(type2_links_df)
        type2_links_pred = []
        if not type2_links_df.empty:
            type2_links_pred = self.predictor.predict(type2_links_df,self.reliable_links.mapping,self.reliable_links.reverse_mapping)    
           
        
    
        
        ## 第二遍循环，标记可疑路由并输出异常事件
        # print(routes)
        for route in routes:
          
            fileds = route.split('|') 
            # timestamp = fileds[1]
            # type = fileds[2]
            # if type != 'A':
            #     continue
            
           
         
            # print(len(fileds))
            # print(fileds)
            # peer_address,peer_asn,prefix,as_path,next_hop,community = fileds[3],fileds[4],fileds[5].strip(),fileds[6],fileds[8],fileds[11]
            datetime,pfx,as_path = fileds[0],fileds[1],fileds[2]
            
            type_1_event = self.rule_engine.check_type1_links(as_path,new_ases) 
            
            type_2_event = None
            if type2_links_pred:
                type_2_event = self.rule_engine.check_type2_links(as_path,type2_links_pred,AS_PATH_len_threshold)
    
            

            if type_1_event:
                type_1_event.update({
                "prefix":prefix,
                # "timestamp":timestamp2date(timestamp),
                "datetime":datetime,
                })
                self.event_manager.add_event1(type_1_event)
            if type_2_event:
                type_2_event.update({
                    "prefix":prefix,
                    # "timestamp":timestamp2date(timestamp),
                    "datetime":datetime,
                })
                self.event_manager.add_event2(type_2_event)
        

def  run_live():     
    if __name__ == '__main__':
        fireye = Fireye()
        fireye.prepare_reliable_links()
        # train_data,test_data = fireye.prepare_dataset() 
        # fireye.predictor.train(train_data,test_data)  
        
        # 
        # 
            
        while True:
                path = get_latest_update_online()
                # path = '/home/pzd/bgp-fake-as-path/tmp/updates.20210820.1240.txt'
                # path = '/home/pzd/bgp-fake-as-path/tmp/rrc00_latest-update.txt'
                print(path)
                fireye.detect(path)
                # fireye.event_manager.show_events()
                fireye.event_manager.write_events()
                
                while not check_if_new_latest_update(): 
                    print("waiting for new update...")
                    time.sleep(60)
                    pass
                # exit()
                
def run_history_tmp(start,end):
    fireye = Fireye()
    fireye.prepare_reliable_links(date=start)
    # train_data,test_data = fireye.prepare_dataset() 
    # fireye.predictor.train(train_data,test_data)  
    
    # 
    # 
    
    for i in range(2,31):
        date = '2021-11-{:02d}'.format(i)
    
        while True:
                # path = get_latest_update_online()
                # path = '/home/pzd/bgp-fake-as-path/tmp/updates.20210820.1240.txt'
                # path = '/home/pzd/bgp-fake-as-path/tmp/rrc00_latest-update.txt'  
                path = f'data/result/exp/{date}_type2_route.txt'
                print(path)
                fireye.detect(path)
                fireye.event_manager.show_events()
                fireye.event_manager.write_events()
                
                # while not check_if_new_latest_update(): 
                #     print("waiting for new update...")
                #     time.sleep(60)
                #     pass
run_history_tmp('2021-11-01','2021-11-30')