# Json_To_Redis

import redis
import json



with open("./usrs.json",'r') as f:
	alist = json.load(f)
	print(alist)

# for names in alist:
# 	r0.lpush("UserName",names)
# 	print(names)
# # print("Done")