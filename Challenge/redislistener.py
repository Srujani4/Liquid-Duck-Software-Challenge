import asyncio
import redis.asyncio as aioredis
import json
from DuckDBManager import DuckDBManager
from logger import redis_logger

redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)
db_manager = DuckDBManager()


REQUEST_STREAM = "request_duck"
RESPONSE_STREAM = "response_duck"


async def listen_to_requests():
    """
    Listen to Redis request stream and process updates.
    """
    print("Starting Redis listener...")
    redis_logger.info("Listening to Redis request stream...")
    while True:
        try:
            print("Waiting for messages on the request stream...")
            messages = await redis_client.xread({REQUEST_STREAM: "$"}, block=5000, count=1)
            print(f"Received message(s): {messages}")
            for stream, message_list in messages:
                for _, message in message_list:
                    request = json.loads(message["data"])
                    print(f"Processing request: {request}")
                    redis_logger.info(f"Processing request: {request}")

                    # Update DuckDB table
                    await db_manager.execute_query_async(
                        f"""
                        UPDATE {request['table']}
                        SET {request['column']} = '{request['value']}'
                        WHERE {request['condition']};
                        """
                    )

                    # Broadcast the success response to the response stream
                    await redis_client.xadd(
                        RESPONSE_STREAM,
                        {"data": json.dumps({"status": "success", "request": request})},
                    )
                    print(f"Broadcasted response for request: {request}")
                    redis_logger.info(f"Broadcasted response for request: {request}")
        except Exception as e:
            print(f"Error processing request stream: {str(e)}")
            redis_logger.error(f"Error processing request stream: {str(e)}")


if __name__ == "__main__":
    asyncio.run(listen_to_requests())
