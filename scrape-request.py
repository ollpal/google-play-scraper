import sys
import json

import boto.sqs
from boto.sqs.message import Message

id = sys.argv[1]

conn = boto.sqs.connect_to_region("eu-west-1")
q = conn.create_queue('google-play-scraper', 360)

m = Message()
m.set_body(json.dumps({'id': id}))

status = q.write(m)
