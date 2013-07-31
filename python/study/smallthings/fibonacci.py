#coding:utf-8
class C(object):
    def __setattr__(self, key, value):
        if key == 'o':
            object.__setattr__(key,"test")
        else:
            object.__setattr__(key,value)

d ={'a':1,"b":2,"o":3}
c = C()
c.a = d['a']
c.b = d['b']
c.o = d['o']
print c
