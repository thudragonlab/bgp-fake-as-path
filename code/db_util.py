from datetime import datetime
import json
from pymongo import MongoClient

with open('db_config.json', 'r') as f:
    db_config = json.load(f)
    print(db_config)
db_name = db_config['db_name']
host = db_config['host']
port = db_config['port']
user = db_config['user']
pwd = db_config['pwd']

collection_name_mapping = {
    'serial1': {
        'db_name': 'caida-as-relationships',
        'collection_name': lambda date: date,
        'col-date_format': "%Y%m%d",
    },
    'irr_WHOIS': {
        'db_name': 'irr_whois',
        'collection_name': 'WHOIS',
        'col-date_format': "WHOIS"
    },
    'type1': {
        'db_name': db_name,
        'collection_name': 'type1_event',
        'col-date_format': "type1_event"
    },
    'type2': {
        'db_name': db_name,
        'collection_name': 'type2_event',
        'col-date_format': "type2_event"
    },
    'type2_aggregated':{
        'db_name': db_name,
        'collection_name': 'type2_aggregated_event',
        'col-date_format': "type2_aggregated_event"
    }
}
mongo_client = MongoClient(host=host,
                           port=int(port),
                           username=user,
                           password=pwd,
                           unicode_decode_error_handler='ignore',
                           maxPoolSize=1024,
                           connect=False)


def get_mongo_db():
    db = mongo_client[db_name]
    return db


gol_db = get_mongo_db()


def get_daily_collection_name(db_mapping_name):
    will_use_collection_name = datetime.utcnow().strftime(collection_name_mapping[db_mapping_name]['col-date_format'])
    return will_use_collection_name

def get_collection_by_gol_db(db_mapping_name):
    return gol_db[collection_name_mapping[db_mapping_name]['collection_name']]

def get_daily_collection(db_mapping_name):
    existColName = mongo_client[collection_name_mapping[db_mapping_name]['db_name']].list_collection_names()
    match_list = []
    for i in existColName:
        try:
            datetime.strptime(i, collection_name_mapping[db_mapping_name]['col-date_format'])
            match_list.append(i)
        except ValueError:
            continue
    match_list.sort(key=lambda x: datetime.strptime(x, collection_name_mapping[db_mapping_name]['col-date_format']).timestamp())
    if len(match_list) != 0:
        will_use_collection_name = match_list[-1]
    else:
        will_use_collection_name = get_daily_collection_name(db_mapping_name)
    return mongo_client[collection_name_mapping[db_mapping_name]['db_name']][will_use_collection_name]



    return db[col_name]
# if __name__ == '__main__':
#     print(get_daily_collection('serial1').name)