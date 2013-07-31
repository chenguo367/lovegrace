#coding:utf8
__author__ = 'chenguo'
__doc__ = """
腾讯笔试题
"""

ask_1 = """
有列表 [1,2,3] 给出一个函数输出
[[1, 3, 2],
[2, 1, 3],
[3, 2, 1]]"""
def fun(_list):
    lenth = len(_list)
    result = [[]]*lenth
    for i in range(lenth):
        for j in range(lenth):
            if not result[i]:
                result[i] = []
            result[i].append( _list[i-j])
    return  result
print ask_1
print fun([1,2,3])

ask_2 = """
定义一个类，获取该类属性，如果该类有这个属性，则返回该属性值，如果没有，则返回属性名称"""
class Example(object):
    test = "This is a example"

    def __getattr__(self, item):
        return item

print ask_2
a = Example()
print a.test
print a.oh_my_god

ask_3 = """
[1,2,3,5,8,...]给一个函数，返回斐波那契数列"""
def fibonacci():
    """生成器"""
    a = b = 1
    yield a
    yield b
    while 1:
        a,b = b,a+b
        yield b
fbnc = fibonacci()
result = list()
j = 0
while j < 10:
    result.append(fbnc.next())
    j += 1
print ask_3
print result

ask_4 = """
计算素数的无限范围值 | 给出一个范围内的所有素数"""
_="""
检查一个正整数N是否为素数，最简单的方法就是试除法，将该数N用小于等于根号N的所有素数去试除，
若均无法整除，则N为素数，参见素数判定法则。
"""
def get_prime(n,prime_list):
    if n < 2 or n in prime_list: return prime_list
    for i in prime_list:
        if i < int(n**0.5)+1:
            if n%i == 0: return prime_list
        else:
            break
    prime_list.append(n)
    print n
    return prime_list
i=0
#种子
prime_list = [2]
while i<100 and 1:
    prime_list  = get_prime(i,prime_list)
    i+=1
print prime_list


