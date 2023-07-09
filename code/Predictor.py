import pandas as pd
import time 
import os

class Predictor:
    def __init__(self):
        self.model_id = 'tmp'

    def train(self, train_data , test_data):
        
        #训练模型
        id = self.model_id
        if os.path.exists(os.path.join('SEAL/Python/model',f'{id}_hyper.pkl')):
            return
        # 创建一个目录
        os.system(f'mkdir -p data/topo/{id}/')
        train_data_path = f'data/topo/{id}/{id}_train.txt'
        test_data_path = f'data/topo/{id}/{id}_test.txt'

        train_data.to_csv(train_data_path, sep='\t', index=False, header=False)
        test_data.to_csv(test_data_path, sep='\t', index=False, header=False)

        s = time.time()
        
        os.system(f'python3.8 SEAL/Python/Main.py  --train-path data/topo/{id}/{id}_train.txt --test-path data/topo/{id}/{id}_test.txt --save-model' )
        # os.system('cd SEAL/Python/; python3.8 Main.py --data-name exp --train-path data/topo/exp/exp_train.txt   --test-path data/topo/exp/exp_test.txt  --save-model')
        e = time.time()
        print('Training cost:',e-s)
        
    
    def predict(self, pred_data,mapping,reverse_mapping):
        id = self.model_id
        print('模型预测中...')
        train_data_path = f'data/topo/{id}/{id}_train.txt'
        test_data_path = f'data/topo/{id}/type2.link'
        pred_data_path = f'data/topo/{id}/{id}_pred.txt'
        
        print(pred_data)

        ## 
        # pred_data = 
        pred_data = pred_data.applymap(lambda x: mapping[str(x)])
        
        
        pred_data.to_csv(test_data_path, sep='\t', index=False, header=False)
        
        os.system(f'python3.8 SEAL/Python/Main.py  --train-path {train_data_path} --test-path {test_data_path} --pred-path {pred_data_path}  --only-predict')
        df_pred = pd.read_csv(f'data/topo/{id}/{id}_pred.txt',sep=' ',header=None)  
        df_pred.columns = ['u','v','pred']
        df_pred['u'] = df_pred['u'].apply(lambda x: reverse_mapping[str(int(x))])
        df_pred['v'] = df_pred['v'].apply(lambda x: reverse_mapping[str(int(x))])
        print(df_pred)
        # df_pred转换为字典，键为（u，v），值为pred
        pred_dict = {}
        for i in range(len(df_pred)):
            u = df_pred.iloc[i]['u']
            v = df_pred.iloc[i]['v']
            pred = df_pred.iloc[i]['pred']
            u,v = min(int(u),int(v)),max(int(u),int(v))
            u,v = str(u),str(v)
            pred_dict[(u,v)] = pred
        return pred_dict
        
        

    # def save(self, path):
    # #     pass
    # # def load(self, path):
    # #     pass

    