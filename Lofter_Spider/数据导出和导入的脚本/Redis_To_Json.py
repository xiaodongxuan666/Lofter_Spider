import redis
import json
import demjson

r0 = redis.Redis(host='127.0.0.1', port=6379,db=0,decode_responses=True)
alist = []
while r0.llen('UserName'):
	i = r0.lpop('UserName')
	print(i)
	alist.append(i)

with open('./usrs.json', 'w') as f:
	f.write(demjson.encode(alist))
#	f.write(json.dumps({"alist":alist}))

print(len(alist))