import os
from utils import *
all = 0

type_1 = {}
type_2 = {}

from RuleEngine import  *
fp0 = open('data/result/exp/type2_event.txt','w')
rule_engine = RuleEngine()
for i in range(2,31):
    cnt = 0
    date = '2021-11-{:02d}'.format(i)
    file = 'data/result/exp/{}_delta_type2.pred'.format(date)
    with open(file) as fp:
        for line in fp:
            u,v,w = line.strip().split(' ')
            if(u,v) not in type_2:
                type_2[(u,v)] = float(w)

    file = 'data/result/exp/{}_type2_route.txt'.format(date)
    with open(file) as fp:
        cnt = 0
        for line in fp:
            datetime_,prefix,as_path,link = line.strip().split('|')
            event = rule_engine.check_type2_links(as_path,type_2)
            if event:
                if event['suspicious links'][0][2]<0.8:
                    event['datetime'] = datetime_
                    event['prefix'] = prefix
                    # print(event)
                    cnt += 1
                    # print(json.dumps(event))
                    fp0.write(json.dumps(event))
                    fp0.write('\n')
        print(cnt)
            # exit()
    
fp0.close()
print(all)