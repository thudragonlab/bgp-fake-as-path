import time
import pybgpstream
import collections

as_path_dict = collections.defaultdict(int)
def get_true_as_path():
    start_time = '2021-11-01 00:00:00'
    until_time = '2021-11-01 01:00:00'
    
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
                            record_type='ribs',  # announcement、rib field中才有as-path，
                            # withdrawal中只有prefix
                            # filter=f'prefix more {event["prefix"]} '
                            # filter =  filter
                            # https://github.com/CAIDA/libbgpstream/blob/master/FILTERING
                            # filter='ipversion 4 and path "_{:}$"'.format(VICTIM_AS),
                        ) 
    for rec in stream.records():
        for elem in rec:
            # print(elem._maybe_field('as-path'))
            as_path_dict[elem._maybe_field('as-path')] += 1
            
s = time.time()
get_true_as_path()
with open('data/AS_PATH.txt', 'w') as f:
    for key in as_path_dict.keys():
        f.write(key)
        f.write('\n')


e = time.time()

print(e-s)