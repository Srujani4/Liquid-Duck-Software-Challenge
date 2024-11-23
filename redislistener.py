import redis
import json
from DuckDBManager import DuckDBManager

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
db_manager = DuckDBManager()

REQUEST_STREAM = "request_duck"
RESPONSE_STREAM = "response_duck"

def listen_to_requests():
    print("Listening to Redis stream...")
    while True:
        messages = redis_client.xread({REQUEST_STREAM: "$"}, block=5000, count=1)
        for _, message_list in messages:
            for _, message in message_list:
                request = json.loads(message["data"])
                db_manager.execute_query(f"""
                    UPDATE {request['table']}
                    SET {request['column']} = '{request['value']}'
                    WHERE {request['condition']};
                """)
                redis_client.xadd(RESPONSE_STREAM, {"data": json.dumps({"status": "success", "request": request})})

listen_to_requests()
