# import subprocess
# import os

# # Paths to your files
# uvicorn_path = "uvicorn"
# mainapi_file = "mainapi:app"
# redis_listener_file = "redislistener.py"


# # Function to start FastAPI server
# def start_fastapi():
#     print("Starting FastAPI server...")
#     subprocess.Popen([uvicorn_path, mainapi_file, "--reload"])


# # Function to start Redis listener
# def start_redis_listener():
#     print("Starting Redis Listener...")
#     subprocess.Popen(["python", redis_listener_file])


# # Function to check if Redis is running
# def check_redis():
#     try:
#         import redis
#         client = redis.Redis(host="localhost", port=6379)
#         if client.ping():
#             print("Redis is running.")
#         else:
#             print("Redis is not running. Please start Redis manually.")
#             os.system("redis-server")
#     except Exception as e:
#         print(f"Error connecting to Redis: {e}")
#         os.system("redis-server")


# if __name__ == "__main__":
#     # Check Redis
#     check_redis()

#     # Start FastAPI and Redis Listener
#     start_fastapi()
#     start_redis_listener()

# from adbc_driver_manager import dbapi

# # Adjust path to your DuckDB driver
# con = dbapi.connect(driver="C:/Users/svatt/libduckdb-windows-amd64/duckdb.dll", 
#                     entrypoint="duckdb_adbc_init", 
#                     db_kwargs={"path": "sales_metrics.duckdb"})

# with con.cursor() as cursor:
#     cursor.execute("SELECT * FROM sales_summary_by_product_family;")
#     result = cursor.fetchall()
#     print(result)

from adbc_driver_manager import dbapi


class DuckDBManager:
    def __init__(self):
        try:
            self.conn = dbapi.connect(
                driver="C:/Users/svatt/libduckdb-windows-amd64/duckdb.dll",
                entrypoint="duckdb_adbc_init",
                db_kwargs={"path": "sales_metrics.duckdb"}
            )
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT 1;")
            print("DuckDB connection established successfully.")
        except Exception as e:
            print(f"Error connecting to DuckDB: {str(e)}")
            raise


