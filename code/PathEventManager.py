import pandas as pd
import json
from db_util import get_collection_by_gol_db,gol_db,get_mongo_db


class PathEventManager:

    def __init__(self) -> None:
        self.event1_list = []
        self.event2_list = []
        self.type2_links = {}
        self.all_new_ases = {}
        self.aggregated_event_dict = {}

    def add_event1(self, event):
        self.event1_list.append(event)

    def add_event2(self, event):
        self.event2_list.append(event)

    def add_links(self, links):
        self.type2_links.update(links)

    def add_new_ases(self, new_ases):
        self.all_new_ases.update(new_ases)

    def show_events(self):
        pd.set_option('display.max_columns', None)
        print(pd.DataFrame(self.event1_list))
        print(pd.DataFrame(self.event2_list))

    # def write_events(self):
    #     if self.event1_list:
    #         col1 = get_collection_by_gol_db('type1')
    #         if col1.name not in gol_db.list_collection_names():
    #             col1.create_index([('timestamp',1)],background=True)
    #         col1.insert_many(self.event1_list)
    #         self.event1_list = []
    #     if self.event2_list:
    #         col2 = get_collection_by_gol_db('type2')
    #         if col2.name not in gol_db.list_collection_names():
    #             col2.create_index([('timestamp',1)],background=True)
    #         col2.insert_many(self.event2_list)
    #         self.event2_list = []
    
    def aggregate_and_write_events(self):
        
        if self.event1_list:
            # print(self.event1_list)
            col1 = get_collection_by_gol_db('type1')
            if col1.name not in gol_db.list_collection_names():
                col1.create_index([('timestamp',1)],background=True)
            col1.insert_many(self.event1_list)
            self.event1_list = []
            
        # 将聚合后的事件放入一个字典中，key为link，value为事件，聚合时，
        # 将相同link的事件放入同一个字典中
        # 注意某个link对应的事件聚合结束的标志为当前update报文中的没有该link的事件
        self.event2_list = sorted(self.event2_list,key=lambda x:x['timestamp'])

        # 记录仍需要聚合的事件
        flags = set()
        # 将当前event2_list中的事件聚合到对应的aggregate_event中。
     
        for event in self.event2_list:
            if  len(event['suspicious links']) > 1:
                print('length longer than 1',event['suspicious_links'])

            for link in event['suspicious links']:
                if link not in self.aggregated_event_dict:
                    aggregated_event = {}
                    aggregated_event['suspicious_link'] = link
                    aggregated_event['timestamp'] = event['timestamp']
                    aggregated_event['datetime'] = event['datetime']
                    aggregated_event[event['prefix']] = [event['suspicious AS-PATH']]
                    aggregated_event['max_score'] = event['score']
                    aggregated_event['reasons'] = event['reasons']
                    aggregated_event['prediction_value'] = link[2]
                    self.aggregated_event_dict[link] = aggregated_event
                    flags.add(link)
                else:
                    pfx,reason,score,timestamp,datetime,as_path= event['prefix'],event['reasons'],event['score'],event['timestamp'],event['datetime'],event['suspicious AS-PATH']
                    self.aggregated_event_dict[link].setdefault(pfx,[])
                    if as_path not in self.aggregated_event_dict[link][pfx]:
                        self.aggregated_event_dict[link][pfx].append(as_path)
                    
                    self.aggregated_event_dict[link]['reasons'] = self.aggregated_event_dict[link]['reasons'] + reason
                    self.aggregated_event_dict[link]['max_score'] = max(self.aggregated_event_dict[link]['max_score'],score)
                    flags.add(link)
        self.event2_list = []
        # 处理结束聚合的事件，将其写入数据库
        keys = list(self.aggregated_event_dict.keys())
        for link in keys:
            if link not in flags:
                self.aggregated_event_dict[link]['reasons'] = list(set(self.aggregated_event_dict[link]['reasons']))
                print(self.aggregated_event_dict[link])
                col_name = 'type2_aggregated'
                # db = get_mongo_db()
                # db.create_collection(col_name)
                col = get_collection_by_gol_db('type2_aggregated')
                if col.name not in gol_db.list_collection_names():
                    col.create_index([('timestamp',1)],background=True)
                col.insert_one(self.aggregated_event_dict[link])
                del self.aggregated_event_dict[link]