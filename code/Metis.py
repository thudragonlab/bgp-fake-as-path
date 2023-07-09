from Predictor import *
from ReliableLinkBase import *
from RuleEngine import *
from PathEventManager import *
import os
## parameters

prediction_threshold = 0.5
AS_PATH_len_threshold = 10


class Metis:

    def __init__(self):
        self.reliable_links = ReliableLinkBase()
        self.predictor = Predictor()
        self.rule_engine = RuleEngine()
        self.event_manager = PathEventManager()
        self.history_as = set()
        self.history_links = set()

    def prepare_reliable_links(self, dir='data/result/exp2', date=None):
        os.makedirs(dir,exist_ok=True)
        if dir and os.path.exists(f'{dir}/reliable_link_set.json'):
            print('load reliable_links from file')
            self.reliable_links.load_all(dir)
        else:
            # 获取当前日期
            now = datetime.datetime.now()
            now = str(now).split(' ')[0]
            # print(date)
            self.reliable_links.generate_reliable_link_set(date=date)
            self.reliable_links.generate_dataset(date=date)
            self.reliable_links.save_all(dir)

    def prepare_dataset(self, dir='data/result/exp2', date=None):
        os.makedirs(dir,exist_ok=True)
        if dir and os.path.exists(f'{dir}/train.txt'):
            print('load dataset from file')
            [train_data, test_data] = self.reliable_links.load_dataset(dir)
            return train_data, test_data
        else:
            # 获取当前日期
            # now = datetime.datetime.now()
            # now = str(now).split(' ')[0]
            # print(now)
            [train_data, test_data] = self.reliable_links.generate_dataset(date)
            self.reliable_links.save_dataset(train_data, test_data, dir)

            return train_data, test_data

    def detect(self, path):
        routes = []
        with open(path, 'r') as fp:
            for line in fp:
                routes.append(line.strip())
        type0_links = set()
        type0_unseen = set()
        type1_links = set()
        type1_unseen = set()
        new_ases = set()
        type2_links = set()
        type2_unseen = set()
        type2_other = set()

        print(len(self.reliable_links.as_set))
        # print(self.reliable_links.as_set)
        # links = {}
        ## 第一遍循环，提取type0和type1的链路
        cnt = 0
        for route in routes:
            # print(route)
            fileds = route.split('|')
            timestamp = fileds[1]
            type = fileds[2]
            if type != 'A':
                continue
            # print(route)
            peer_address, peer_asn, prefix, as_path, next_hop, community = fileds[3], fileds[4], fileds[5].strip(
            ), fileds[6], fileds[8], fileds[11]
            # datetime,prefix,as_path = fileds[0],fileds[5],fileds[6]
            ASes = as_path.split(' ')
            # print(as_path)
            for i in range(len(ASes) - 1):
                # 将u中的{和}去除
                u, v = ASes[i], ASes[i + 1]
                if ',' in u or ',' in v:
                    continue
                u = u.replace('{', "").replace('}', "")
                v = v.replace('{', "").replace('}', "")
                if not u or not v:
                    continue
                u, v = min(int(u), int(v)), max(int(u), int(v))
                if u == v:
                    continue
                u, v = str(u), str(v)
                x, y = u in self.reliable_links.as_set, v in self.reliable_links.as_set
                # print(x,y)

                if x and y:
                    if (u, v) in self.reliable_links or (v,u) in self.reliable_links:
                        type0_links.add((u, v))
                        if (u,v) not in self.history_links and (v,u) not in self.history_links:
                            type0_unseen.add((u,v))
                    else:
                        if u not in self.reliable_links.mapping or v not in self.reliable_links.mapping:
                            type2_other.add((u, v))
                            continue
                        type2_links.add((u, v))
                        if (u,v) not in self.history_links and (v,u) not in self.history_links:
                            type2_unseen.add((u,v))
                    # links[(u,v)] = [0]
                else:
                    if u not in self.reliable_links.as_set:
                        new_ases.add(u)
                    if v not in self.reliable_links.as_set:
                        new_ases.add(v)
                    # print((u,v))
                    
                    type1_links.add((u, v))
                    if (u,v) not in self.history_links and (v,u) not in self.history_links:
                        type1_unseen.add((u,v))

                self.history_as.add(u)
                self.history_as.add(v)
                
                self.history_links.add((u,v))

        print("Number of new ASes:", len(new_ases))
        print("Number of Type-0 links:", len(type0_links),len(type0_unseen))
        print("Number of Type-1 links:", len(type1_links),len(type1_unseen))
        print("Number of Type-2 links", len(type2_links),len(type2_unseen))
        print("Number of Type-2 other", len(type2_other))

        # ,len(type0_links),len(type1_links),len(type2_links),len(type2_other))
        if len(type1_links) == 0 and len(type2_links) == 0:
            print('No Type-1 links and Type-2 links')
            return

        type2_links_df = pd.DataFrame(type2_links, columns=['u', 'v'])

        print(type2_links_df)
        type2_links_pred = {}
        if not type2_links_df.empty:
            type2_links_pred = self.predictor.predict(type2_links_df, self.reliable_links.mapping,
                                                      self.reliable_links.reverse_mapping)
        
        # 将预测值大于0.8的Type-2链路加入reliable_links中，以防止重复检测

        for u, v in type2_links_pred:
            if type2_links_pred[(u, v)] > 0.8:
                self.reliable_links.reliable_link_set.add((u,v))

            # print('type2_links_pred',type2_links_pred)
        # with open('data/topo/tmp/tmp_pred.txt','r') as f:
        #     for i in f.readlines():
        #         i_s = i.strip().split(' ')
        #         type2_links_pred[(i_s[0],i_s[1])]  = i_s[2]
        # print('type2_links_pred',type2_links_pred)
        ## 第二遍循环，标记可疑路由并输出异常事件
        # print(routes)
        for route in routes:

            fileds = route.split('|')
            timestamp = fileds[1]
            type = fileds[2]
            if type != 'A':
                continue

            # print(len(fileds))
            # print(fileds)
            peer_address,peer_asn,prefix,as_path,next_hop,community = fileds[3],fileds[4],fileds[5].strip(),fileds[6],fileds[8],fileds[11]


            type_1_event = self.rule_engine.check_type1_links(as_path, new_ases)

            type_2_event = None
            
            if type2_links_pred:
                type_2_event = self.rule_engine.check_type2_links(as_path, type2_links_pred, AS_PATH_len_threshold)
                # print(f'type_2_event {type_2_event} ')
                # print(f'type_1_event {type_1_event} ')

            if type_1_event:
                type_1_event.update({
                    "prefix": prefix,
                    # "timestamp":timestamp2date(timestamp),
                    "datetime": timestamp2date(timestamp),
                    "timestamp":int(timestamp)
                })
                self.event_manager.add_event1(type_1_event)
            if type_2_event:
                type_2_event.update({
                    "prefix": prefix,
                    # "timestamp":timestamp2date(timestamp),
                    "datetime": timestamp2date(timestamp),
                    "timestamp":int(timestamp)
                })
                self.event_manager.add_event2(type_2_event)


def run_live():
    if __name__ == '__main__':
        metis = Metis()
        now = datetime.datetime.now()
        now = str(now).split(' ')[0]
        metis.prepare_reliable_links(date=now)
        train_data,test_data = metis.prepare_dataset()
        metis.predictor.train(train_data,test_data)

        #
        #

        while True:
            path = get_latest_update_online()
            # path = '/home/pzd/bgp-fake-as-path/tmp/updates.20210820.1240.txt'
            # path = '/home/pzd/bgp-fake-as-path/tmp/rrc00_latest-update.txt'
            print(path)
            metis.detect(path)
            # metis.event_manager.show_events()
            metis.event_manager.aggregate_and_write_events()

            while not check_if_new_latest_update():
                print("waiting for new update...")
                time.sleep(60)

            # exit()


def run_history_tmp(start, end):
    metis = Metis()
    metis.prepare_reliable_links(date=start)
    # train_data,test_data = metis.prepare_dataset()
    # metis.predictor.train(train_data,test_data)

    #
    #

    # for i in range(2,31):
    # date = '2021-11-{:02d}'.format(i)

    while True:
        path = get_latest_update_online()
        # path = '/home/pzd/bgp-fake-as-path/tmp/updates.20210820.1240.txt'
        # path = '/home/pzd/bgp-fake-as-path/tmp/rrc00_latest-update.txt'
        # path = f'data/result/exp/{date}_type2_route.txt'
        print(path)
        metis.detect(path)
        metis.event_manager.show_events()
        metis.event_manager.aggregate_and_write_events()

        while not check_if_new_latest_update():
            print("waiting for new update...")
            time.sleep(60)
            pass


run_live()