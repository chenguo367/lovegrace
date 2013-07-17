#coding:utf-8
__doc__ = """24点(或n点)的计算
hoxide <hoxide_dirac@yahoo.com.cn> 发起
题面
就是利用加减乘除以及括号将给出的四张牌组成一个值为24的表达式 现在可以变化为 1 5 6 7 用+-*/ 算出21
http://wiki.woodpecker.org.cn/moin/PyProgramGames/24point
"""

#给定n个数字，通过其间四则运算得到数m
# #######################################################################
# funs = [ lambda x, item: (x+item[0],
#                                str(x)+'+('+item[1]+')'
#                               ),
#       lambda x, item: (x-item[0],
#                                str(x)+'-('+item[1]+')'
#                               ),
#       lambda x, item: (item[0]-x,
#                                '('+item[1]+')-'+str(x)
#                               ),
#       lambda x, item: (x*item[0],
#                                str(x)+'*('+item[1]+')'
#                               ),
#       lambda x, item:   (item[0]==0 and (0,'ZZZ')) or \
#                         (x/item[0],
#                                str(x)+'/('+item[1]+')'
#                               ),
#       lambda x, item:   (x==0 and (0,'ZZZ')) or \
#                         (item[0]/x,
#                                '('+item[1]+')/'+str(x)
#                               )
# ]
#
# def con(num):
#     l = len(num)
#     p = list()
#     if l==1: return {num[0]:str(num[0])}
#     for i in range(l):
#         for f in funs:
#             p += map(lambda item: f(num[i],item),
#                        con(num[:i]+num[i+1:]).items()
#                     )
#     return dict(p)
#
# results =  con(map(float,[1,5,6,7]))
# print results.get(21.0,0)
# #######################################################################
# 参考以上代码后的理解
_="""归纳法：
给定1个数，fun(a)    =>[a] 元素的结构:element = (num,str(num),)
给定2个数，fun(a,b)  =>[a+b,a-b,a*b,a/b,b-a,b/a]
给定3个数，fun(a,b,c)=>[fun(a,fun(b,c)),fun(fun(a,c),b),fun(fun(a,b),c)]
"""
#定义结果数组结构
#element = (num,str(num),)
class element():
    def __init__(self,i,string=''):
        self.num = i
        if not string:
            self.str = str(int(i))
        else:
            self.str = string

    def totuple(self):
        #计算完成，取出结果销毁对象
        here = (self.num,self.str[1:-1],)#去掉首尾两端的括号
        del self
        return here
#================================================================================
#开始定义操作函数
#参数a :数字
#参数b :element
#返回: element
def operate_1(a,b):
    return element(a+b.num,"(%s+%s)"%(int(a),b.str))
def operate_2(a,b):
    return element(a-b.num,"(%s-%s)"%(int(a),b.str))
def operate_3(a,b):
    return element(b.num-a,"(%s-%s)"%(b.str,int(a)))
def operate_4(a,b):
    return element(a*b.num,"(%s*%s)"%(int(a),b.str))
def operate_5(a,b):
    #被除数等于0，跳过
    if b.num==0:
        return None
    return element(a/b.num,"(%s/%s)"%(int(a),b.str))
def operate_6(a,b):
    if a==0:
        #被除数等于0，跳过
        return None
    return element(b.num/a,"(%s/%s)"%(b.str,int(a)))

operate_list = [operate_1,operate_2,operate_3,operate_4,operate_5,operate_6]
#==============================================================================
#计算结果处理
def getresult(func,*args):
    result = func(map(float,list(args)))
    #列表去重
    return list(set([el.totuple() for el in result]))

def result_to_dict(result,keepall = False):
    """列表结果转换为字典格式
    keepall :是否保留所有可能的运算方式。
    """
    if not keepall:
        return dict(result)
    else:
        p = dict().fromkeys([r[0] for r in result])
        for k,v in result:
            if not p[k]:
                p[k] = [v]
            else:
                p[k].append(v)
        return p


def compute(numlist):
    """
    计算数字列表的所有运算结果
    """
    def do_operate(num,result_list,p):
        """
        将数字num与结果列表中的元素进行四则运算，将结果放回结果列表
        """
        for el in result_list:
            for op in operate_list:
                #去除重复的结果
                if num == el.num and op in [operate_3,operate_6]:
                    continue
                result_el = op(num,el)
                if result_el is not None :p.append(result_el)
        return p

    lenth = len(numlist)
    p = list()
    if lenth  ==1:
        return [element(numlist[0])]
    for i in xrange(lenth):
        num = numlist[i]
        #fun(n-1)
        #去除一个数字后，剩余的数字集合
        remain_list = numlist[:i]+numlist[i+1:]
        results_list = compute(remain_list)
        do_operate(num,results_list,p)
        #去除重复操作(仅剩2个数的时候)
        if lenth == 2:
            break
    return p
func = compute
#=================================================================================
#config
target = 21
print_all = True
args = (13,13,11,12)
#=================================================================================
#封装开始计算24点入口
def count_21_point(target,print_all,args):
    a = getresult(func,*args)
    b = result_to_dict(a,print_all)
    return b.get(float(target),'')
#=================================================================================
#封装输出流程
if __name__ == "__main__":
    print ("your number :%s"+",%s"*(len(args)-1)) %args
    print "target number :%d"%target
    solution = count_21_point(target,print_all,args)
    if not solution:
        print "no solution..."
    else:
        print "the solution :"
        if print_all:
            print '\n'.join(solution)
        else:
            print solution