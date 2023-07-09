
from db_util import get_collection_by_gol_db
from utils import *
def Damerau_Levenshtein_edit_distance(str1,str2):
    len1 = len(str1)
    len2 = len(str2)
    d = [[0 for i in range(len2+1)] for j in range(len1+1)]
    for i in range(len1+1):
        d[i][0] = i
    for j in range(len2+1):
        d[0][j] = j
    for i in range(1,len1+1):
        for j in range(1,len2+1):
            if str1[i-1] == str2[j-1]:
                d[i][j] = d[i-1][j-1]
            else:
                d[i][j] = min(d[i-1][j]+1,d[i][j-1]+1,d[i-1][j-1]+1)
            if i>1 and j>1 and str1[i-1] == str2[j-2] and str1[i-2] == str2[j-1]:
                d[i][j] = min(d[i][j],d[i-2][j-2]+1)
    return d[len1][len2]
    
    
    
class RuleEngine:
    def __init__(self):
        self.registered_asn = set()
        self.ixp_list = set()
        # self.prediction_threshold = 0.1
        # self.as_path_length_threshold = 9
        with open('data/irr/20211001_as_dict.json') as fp:
            self.irr_as_dict = json.load(fp) 
            # self.registered_asn = set(self.irr_as_dict.keys())
        with open('data/ihr_hegemony_ipv4_global_2022-01-01.json', 'r') as fp:
            self.hegemony_dict = json.load(fp)
        self.checked_ases = set()
        self.checked_type2_links = set()
        self.checked_as_path =set()
        self.whois_db = get_collection_by_gol_db('irr_WHOIS')
        self.registered_asn = set()

        print(len(self.registered_asn))
    def check_type1_links(self,as_path,new_ases):
        ASes = as_path.split(' ')
        for asn in ASes[::-1]:
            if asn in new_ases:
                if ',' in asn or '{' in asn:
                    continue
                # 新出现的ASN未注册
                if  asn in self.checked_ases:
                    continue
                self.checked_ases.add(asn)
                # # 新出现的ASN为私有ASN
                if int(asn)>= 64512 and int(asn)<=65535 or int(asn)>=4200000000 and int(asn) <=4294967294:
                    # continue
                    return {"suspicious AS": asn ,"suspicious AS-PATH":as_path,"reason":f"ASN{asn} is reserved ASN."}
                
                elif asn not in self.registered_asn:
                    if self.whois_db.find_one({'aut-num':int(asn)}):
                        self.registered_asn.add(asn)
                        continue
                    return {"suspicious AS": asn ,"suspicious AS-PATH":as_path,"reason":f"ASN{asn} is not registered."}

             
                # 新出先的ASN不在AS-PATH最后一跳
                elif asn != ASes[-1] and asn not in self.ixp_list:
                    return {"suspicious AS": asn ,"suspicious AS-PATH":as_path,"reason":f"ASN{asn} is not the last hop."}
                else:
                    # print("okk")
                    return None
                
        return None


                
    
    def check_type2_links(self,as_path,type2_links_result,length_threshold = 9):
        # print(as_path,length_threshold)
        
        
        ASes = as_path.split(' ')
        flag = False
        event = {"suspicious links":[],"suspicious AS-PATH": as_path,"reasons": [],"score":0}
        for i in range(len(ASes)-1,0,-1):
            u,v = ASes[i-1],ASes[i]
            if u == v:
                continue
            if '{' in u or '{' in v:
                continue 
            u,v = min(int(u),int(v)),max(int(u),int(v))
            
            
            u,v = str(u),str(v)
            if (u,v) in self.checked_type2_links:
                continue
            self.checked_type2_links.add((u,v))
            
            if as_path in self.checked_as_path:
                continue 
            self.checked_as_path.add(as_path)
            # print(as_path,'|',u,v,type2_links_result)
            
            # print(u,v,type2_links_result)
            # exit()
            if (u,v) in type2_links_result:
                flag = True
                w = type2_links_result[(u,v)]
                # print('okkk')
                # AS-PATH长度约束，可能是恶意攻击者插入很多无关ASN
                if (u,v) not in event['suspicious links']:
                    event['suspicious links'].append((u,v,w))
                if len(set(ASes)) > length_threshold: 
                    event['level'] = "high"
                    event['score'] += 1
                    event['reasons'].append("AS-PATH is too long") 
                # Type-2链路最后一跳是单数字ASN，可能是错误配置
                if i == len(ASes)-1 and int(ASes[i]) < 10:
                    event['level'] = "high"
                    event['score'] += 1
                    event['reasons'].append("The last hop is single-digital ASN") 
                # Type-2链路两端AS编辑距离小于等于1,可能是错误配置
                if Damerau_Levenshtein_edit_distance(u,v) <=1:
                    event["level"] = "high"
                    event['score'] += 1
                    event['reasons'].append("The edit distance of ASNs in the link is 1") 
                # Type-2链路在环路中，可能是BGP投毒
                if loop([u,v],ASes): 
                    event["level"] = "high"
                    event['score'] += 1
                    event['reasons'].append("There exists loop in the AS-PATH and the suspicious link is in the loop.") 
                    
                # AS-PATH违反valley-free，可能是恶意攻击者插入无关ASN或者路由泄露
                if valley(ASes,self.hegemony_dict)[1]:
                    a,b,c = valley(ASes,self.hegemony_dict)[0]
                    event["level"] = "high"
                    event['score'] += 1
                    event['reasons'].append(f"The AS-PATH violates valley-free rule:'({a},{b},{c}).")
                # AS-PATH同国流量出现绕路情况，可能是路由泄露或者路由劫持
                if country_not_continuous(self.irr_as_dict,as_path.split(' '))[0]:
                    # print(country_not_continuous)
                    flag,country,[asn1,asn2] = country_not_continuous(self.irr_as_dict,as_path.split(' '))
                    event["level"] = "high"
                    event['score'] += 1
                    event['reasons'].append(f"Domestic traffic ({country},{asn1},{asn2}) detour.")
                
                # Type-2链路处于AS-PATH末尾，且最后两个国家同国，很可能是某个AS与国内某个ISP建立互联，或者备份链路被观点到
                if i == len(ASes)-1 and self.irr_as_dict.get(u,{'country':0})['country'] == self.irr_as_dict.get(v,{'country':'1'})['country']:
                    event.update({
                        "level":"low",
                    })
                    event['score'] -= 4
                    event['reasons'].append(f"Suspicious links is at the end of the AS-PATH and a demostic link ({self.irr_as_dict.get(u,{'country':0})['country']}).")
                elif  self.irr_as_dict.get(u,{'country':0})['country'] == self.irr_as_dict.get(v,{'country':'1'})['country']:
                    event['score'] -=2 
                    event['level'] = "medium"
                # else: # 上面条件都不满足，则是medium suspicion
                #     event.update({
                #         "level":"medium",
                #     })
                #     # event['score'] -= 1
                #     event['reasons'].append(f"No matched rule.")
        if flag:
            return event
        else:
            return None 


