
import dis
import sys
import textwrap
import types
import unittest
import six
import json
import pika
import redis
import pickle




code = '''def add(a,b):
    return a+b
'''


code = compile(code, "step<%s>" % id, "exec", 0, 1)
exec(code)

class VM(object):

    def __init__(self, r):
        self.vars = {}
        self.r = r

    def setappid(self,appid):
        self.appid = appid
        self.vars = self.r.get(appid)
        if self.vars is None:
            self.vars = {}
        else:
            self.vars = pickle.loads(self.vars)
        #print('appid', appid, 'vars:', self.vars)
    def updatevars(self):
        self.r.set(self.appid,pickle.dumps(self.vars))

    def reset(self, appid):
        self.vars = {}

    def isvar(self,varname):
        return varname in self.vars.keys()

    def getvar(self,varname):
        return self.vars[varname]
    def setvar(self,varname, val):
        self.vars[varname] = val


    def getmethod(self,method_name):
        possibles = globals().copy()
        possibles.update(locals())
        method = possibles.get(method_name)
        if not method:
            raise NotImplementedError("Method %s not implemented" % method_name)
        return method

    def evalstep(self,step):
        params = step['in']
        for i,p in enumerate(params):
            if type(p) == str:
                if self.isvar(p):
                    params[i] = self.getvar(p)
                    #print('r=',params)
        method = self.getmethod(step['call'])
        if step['out'] == 'return':
            return method(*params)
        k = 'var.'+step['out']
        self.setvar(k,method(*params))
        self.updatevars()
        return None

    def eval(self,json_str):
        js = json.loads(json_str)
        out = []
        if type(js) == list:
            for step in js:
                r = self.evalstep(step)
                if r is not None:
                    out.append(r)
        else:
            r = self.evalstep(js)
            if r is not None:
                    return json.dumps(r)
            return None
            #print('Step:',out)
        if len(out) > 0:
            out = json.dumps(out)
            return out
        return None


r = redis.Redis(host='localhost', port=6379, db=0)
vm = VM(r)


connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))

channel = connection.channel()
channel.queue_declare(queue='bss')
print (' [*] Waiting for messages. To exit press CTRL+C')

import time

def callback(ch, method, properties, body):
    appid = properties.app_id
    try:
        vm.setappid(appid)
        res = vm.eval(body)
        if res is not None:
            #print('Result send', res)
            ch.basic_publish(exchange='',
                             routing_key=properties.reply_to,
                             #properties=pika.BasicProperties(result = res),
                             body=str(res) )
    except:
        print('Wrong data in messsage:', body)
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(callback,
                      queue='bss',
                      no_ack=False)

try:
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()


connection.close()
