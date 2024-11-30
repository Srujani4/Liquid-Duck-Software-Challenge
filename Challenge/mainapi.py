from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
import redis.asyncio as aioredis
# import json
from typing import Optional
from logger import api_logger
from DuckDBManager import DuckDBManager
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan to manage startup and shutdown processes 
    for Redis and DuckDB.
    """
    print("Starting application lifespan...")

    # Startup: Test Redis and DuckDB connections
    try:
        await redis_client.ping()
        print("Connected to Redis successfully.")
        api_logger.info("Redis connection successful.")
    except Exception as e:
        print(f"Redis connection failed: {e}")
        api_logger.error(f"Redis connection failed: {e}")
        raise RuntimeError("Redis connection failed. Check your Redis server.")

    try:
        await db_manager.execute_query_async("SELECT 1;")
        print("Connected to DuckDB successfully.")
        api_logger.info("DuckDB connection successful.")
    except Exception as e:
        print(f"DuckDB connection failed: {e}")
        api_logger.error(f"DuckDB connection failed: {e}")
        raise RuntimeError("DuckDB connection failed.DuckDB is accessible.")

    # Allow application to run
    yield

    # Shutdown: Clean up Redis and ensure all resources are released
    print("Shutting down application lifespan...")
    try:
        await redis_client.close()
        print("Redis connection closed.")
        api_logger.info("Redis connection closed.")
    except Exception as e:
        print(f"Error closing Redis connection: {e}")
        api_logger.error(f"Error closing Redis connection: {e}")

    # Additional cleanup for DuckDB (if needed)
    try:
        db_manager.conn.close()
        print("DuckDB connection closed.")
        api_logger.info("DuckDB connection closed.")
    except Exception as e:
        print(f"Error closing DuckDB connection: {e}")
        api_logger.error(f"Error closing DuckDB connection: {e}")

    print("Application lifespan shutdown complete.")

# Initialize FastAPI app with the lifespan
app = FastAPI(lifespan=lifespan)

# Initialize Async Redis client
redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)

# Initialize DuckDB Manager
db_manager = DuckDBManager()

# Redis streams
REQUEST_STREAM = "request_duck"
RESPONSE_STREAM = "response_duck"


# Pydantic model for the request body
class UpdateRequest(BaseModel):
    table: str = Field(..., description="Name of the table to update")
    column: str = Field(..., description="Column to update")
    value: str = Field(..., description="New value to set")
    condition: str = Field(..., description="SQL condition for rows to update")
    level: Optional[int] = Field(None, description="Grouping level for hierarchical updates")


@app.get("/")
async def read_root():
    """
    Root endpoint for testing server availability.
    """
    api_logger.info("Root endpoint hit successfully.")
    return {"message": "Welcome to the Liquid Duck API!"}


# @app.post("/update_cell")
# async def update_cell(request: UpdateRequest):
#     """
#     Update a specific cell in the database and propagate changes if necessary.
#     """
#     try:
#         # Extract data from the validated request
#         table = request.table
#         column = request.column
#         value = request.value
#         condition = request.condition
#         level = request.level

#         print(f"Received data - Table: {table}, Column: {column}, Value: {value}, Condition: {condition}, Level: {level}")
#         api_logger.info(f"Processing update request for table {table}.")

#         # Test database connectivity
#         await db_manager.execute_query_async("SELECT 1;")
#         print("DuckDB connected successfully.")

#         # Execute the update query asynchronously
#         await db_manager.execute_query_async(
#             f"""
#             UPDATE {table}
#             SET {column} = '{value}'
#             WHERE {condition};
#             """
#         )
#         print(f"Update query executed successfully for {table}.")

#         # Handle proportional rebalance for hierarchical updates
#         if table == "sales_summary_by_product_family" and level is not None:
#             api_logger.info(f"proportional rebalance for level {level}.")
#             await db_manager.proportional_rebalance_async(level, int(value))

#         # Broadcast the changes to Redis response stream
#         await redis_client.ping()
#         print("Redis connected successfully.")
#         await redis_client.xadd(
#             RESPONSE_STREAM,
#             {
#                 "table": table,
#                 "column": column,
#                 "value": value,
#                 "condition": condition,
#                 "level": str(level) if level is not None else "null",
#             }
#         )
#         print(f"Changes broadcasted to Redis stream {RESPONSE_STREAM}.")

#         api_logger.info(f"updated {table}:{column}={value} WHERE {condition}.")
#         return {"status": "success", "message": f"Updated {table}"}

#     except HTTPException as e:
#         api_logger.warning(f"HTTPException while update_cell: {str(e)}")
#         raise e
#     except Exception as e:
#         api_logger.error(f"Unexpected server error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
@app.post("/update_cell")
async def update_cell(request: UpdateRequest):
    """
    Update a specific cell in the database and propagate changes if necessary.
    """
    try:
        # Extract data from the validated request
        table = request.table
        column = request.column
        value = request.value
        condition = request.condition
        level = request.level

        # Validate critical fields
        if not table or not column or not condition:
            raise HTTPException(status_code=400, detail="Invalid input: Missing required fields.")

        print(f"Received data - Table: {table}, Column: {column}, Value: {value}, Condition: {condition}, Level: {level}")
        api_logger.info(f"Processing update request for table {table}.")

        # Test database connectivity
        await db_manager.execute_query_async("SELECT 1;")
        print("DuckDB connected successfully.")

        # Execute the update query asynchronously
        try:
            await db_manager.execute_query_async(
                f"""
                UPDATE {table}
                SET {column} = '{value}'
                WHERE {condition};
                """
            )
            print(f"Update query executed successfully for {table}.")
        except Exception as query_error:
            api_logger.error(f"Query execution error: {str(query_error)}")
            raise HTTPException(status_code=500, detail="Query execution failed.")

        # Handle proportional rebalance for hierarchical updates
        if table == "sales_summary_by_product_family" and level is not None:
            api_logger.info(f"proportional rebalance for level {level}.")
            await db_manager.proportional_rebalance_async(level, int(value))

        # Broadcast the changes to Redis response stream
        try:
            await redis_client.ping()
            print("Redis connected successfully.")
            await redis_client.xadd(
                RESPONSE_STREAM,
                {
                    "table": table,
                    "column": column,
                    "value": value,
                    "condition": condition,
                    "level": str(level) if level is not None else "null",
                }
            )
            print(f"Changes broadcasted to Redis stream {RESPONSE_STREAM}.")
        except Exception as redis_error:
            api_logger.error(f"Redis broadcast error: {str(redis_error)}")
            raise HTTPException(status_code=500, detail="Failed to broadcast changes to Redis.")

        api_logger.info(f"updated {table}:{column}={value} WHERE {condition}.")
        return {"status": "success", "message": f"Updated {table}"}

    except HTTPException as e:
        api_logger.warning(f"HTTPException while update_cell: {str(e)}")
        raise e
    except Exception as e:
        api_logger.error(f"Unexpected server error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.get("/get_updates")
async def get_updates():
    """
    Retrieve updates from Redis response stream for multi-user sync.
    """
    try:
        api_logger.info("Fetching updates from Redis response stream...")
        updates = await redis_client.xrange(RESPONSE_STREAM)
        api_logger.info("Fetched updates successfully.")
        return {"status": "success", "updates": updates}
    except Exception as e:
        api_logger.error(f"Error fetching updates: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Global error occurred: {exc}")  
    api_logger.error(f"Global error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    api_logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )
