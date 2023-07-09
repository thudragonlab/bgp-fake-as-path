import os
from utils import *
all = 0

type_1 = {}
type_2 = {}

from RuleEngine import  *
fp0 = open('data/result/exp/type1_event.txt','w')
rule_engine = RuleEngine()
for i in range(2,31):
    cnt = 0
    date = '2021-11-{:02d}'.format(i)
    # file = 'data/result/exp/{}_delta_type1.pred'.format(date)
    # with open(file) as fp:
    #     for line in fp:
    #         u,v,w = line.strip().split(' ')
    #         if(u,v) not in type_2:
    #             type_2[(u,v)] = float(w)

    file = 'data/result/exp/{}_type1_route.txt'.format(date)
    with open(file) as fp:
        cnt = 0
        for line in fp:
            datetime_,prefix,as_path,link,new_as = line.strip().split('|')
            # print(line)
            event = rule_engine.check_type1_links(as_path,new_ases=[new_as])
            if event:
                # print(event)
                cnt += 1
            #     if event['suspicious links'][0][2]<0.8:
            #         event['datetime'] = datetime_
            #         event['prefix'] = prefix
            #         # print(event)
            #         cnt += 1
            #         # print(json.dumps(event))
                fp0.write(json.dumps(event))
                fp0.write('\n')
        print(cnt)
            # exit()
    
fp0.close()
print(all)