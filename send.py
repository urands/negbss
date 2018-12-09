
import sys
#!/usr/bin/env python
import pika

import numpy as np

import json

import time


appid = 'saddsdasdas'


reply_to = 'amq.rabbitmq.'+ appid 

connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='bss')

result = channel.queue_declare(exclusive=True)

callback_queue = result.method.queue

props = pika.BasicProperties(app_id=appid, 
                                  content_type='application/json',
                                  reply_to=callback_queue)


channel.basic_qos(prefetch_count=1)

json_str = '''
[
  ,
  { "in" : [ 5, 6],  "call" : "add",  "out" : "b" },
  { "in" : [ "var.a", 5 ], "call" : "add",  "out" : "return" }

]
'''


def genmsg(count = 10):
    l = []
    l.append( { 'in': [ 1, 1 ], 'call':'add', 'out':'a' } )
    for i in range(count):
        l.append( { 'in': [ 'var.a', 1 ], 'call':'add', 'out':'a' } )
    l.append( { 'in': [ 'var.a', 1 ], 'call':'add', 'out':'return' } )
    return l


messages = ['{ "in" : [ 1, 1],  "call" : "add",  "out" : "a" }',
            '{ "in" : [ "var.a", 1],  "call" : "add",  "out" : "a" }',
            '{ "in" : ["var.a", 1],  "call" : "add",  "out" : "a" }',
            '{ "in" : [ "var.a", 1],  "call" : "add",  "out" : "a" }',
            '{ "in" : [ "var.a", 1],  "call" : "add",  "out" : "a" }',
            '{ "in" : [ "var.a", 1],  "call" : "add",  "out" : "a" }',
            '{ "in" : [ "var.a", 1],  "call" : "add",  "out" : "return" }'
             ]

messages = json.dumps( genmsg(20000))

#print( messages )




def on_client_rx_reply_from_server(ch, method_frame, properties, body):
    print ('RPC Client got reply:', json.loads(body) )
    # NOTE A real client might want to make additional RPC requests, but in this
    # simple example we're closing the channel after getting our first reply
    # to force control to return from channel.start_consuming()
    print ('RPC Client says bye')


    ch.close()


channel.basic_consume(on_client_rx_reply_from_server, no_ack=True,
                                   queue=callback_queue)



if type(messages) is list:
    for message in messages:
        #message =  "Hello World" + '.'*i
        channel.basic_publish(exchange='',
                          routing_key='bss',
                          body=message,
                          properties = props)
        print (" [x] Sent %r" % (message,))
else:
     channel.basic_publish(exchange='',
                          routing_key='bss',
                          body=str(messages),
                          properties = props)

start_time = time.time()


try:
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()

print("--- %s seconds ---" % (time.time() - start_time))

connection.close()
