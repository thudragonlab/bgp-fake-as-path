
def _init():#初始化
    global _global_dict
    _global_dict = {}
 
 
def set_global_var(key,value):
    """ 定义一个全局变量 """
    _global_dict[key] = value
 
 
def get_global_var(key,defValue=None):
    """获得一个全局变量,不存在则返回默认值"""
    try:
        return _global_dict[key]
    except KeyError:
        print(f"warning,no such global var:{key}")