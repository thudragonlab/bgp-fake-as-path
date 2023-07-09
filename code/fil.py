
import json


for i in range(2,31):
    count = {'low':0,'high':0,'medium':0}
    link = [set(),set(),set()]
    m = {'low':0,'medium':1,'high':2}
    cnt1 = 0
    cnt2 = 0
    checked_link = set()
    with open('data/result/exp/type2_event.txt') as fp:
        for line in fp:
            event = json.loads(line.strip())

            date = '2021-11-{:02d}'.format(i)
            if event['datetime'].startswith(date):
                # print(event)
                if event['score'] == 0:
                    event['level'] = 'medium'
                count[event['level']] +=1
                if event['suspicious links'][0][0] in checked_link:
                    continue
                checked_link.add(event['suspicious links'][0][0])
                link[m[event['level']]].add(event['suspicious links'][0][0])
                if event['level'] == 'high':
                    flag = False
                    for reason in event['reasons']:
                        if 'loop' in reason or 'distance' in reason or 'single' in reason:
                            flag = True
                    if flag:
                        cnt1 += 1
                    else:
                        cnt2 += 1 
    # print(count)
    print(cnt1,cnt2)
    lens = [len(x) for x in link]
    # print(lens)