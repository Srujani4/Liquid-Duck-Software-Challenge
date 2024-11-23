from fastapi import FastAPI, HTTPException
import redis
import json
import sys
from typing import Optional

# Include the challenge path for custom modules

sys.path.append(r"C:\Users\svatt\Liquid Duck Challenge")


# Import the DuckDBManager and logger
from DuckDBManager import DuckDBManager
from logger import api_logger


# Initialize FastAPI app
app = FastAPI()

# Initialize Redis client
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

# Initialize DuckDB Manager
db_manager = DuckDBManager()

# Redis streams
REQUEST_STREAM = "request_duck"
RESPONSE_STREAM = "response_duck"

# Default route for root endpoint
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Liquid Duck API!"}

@app.post("/update_cell")
async def update_cell(
    table: str,
    column: str,
    value: str,
    condition: str,
    parent_id: Optional[int] = None
):
    """
    Update a specific cell in the database and propagate changes if necessary.
    """
    try:
        if not table or not column or not value or not condition:
            raise HTTPException(status_code=400, detail="Invalid input parameters")

        # Logging requst
        api_logger.info(f"Received update request for {table}: {column} = {value} WHERE {condition}")

        # update query execution
        await db_manager.execute_query_async(f"""
            UPDATE {table}
            SET {column} = '{value}'
            WHERE {condition};
        """)

        # Handle proportional rebalance for hierarchical updates
        if table == "sales_summary_by_product_family" and parent_id is not None:
            await db_manager.proportional_rebalance_async(parent_id, int(value))  # Use DuckDBManager's method

        # Handle inter-table dependencies
        await db_manager.update_dependencies_async(table, column, value, condition)

        # Add the update to the response stream for broadcasting
        await redis_client.xadd(RESPONSE_STREAM, {"data": json.dumps({
            "table": table,
            "column": column,
            "value": value,
            "condition": condition
        })})

        # Log success and return response
        api_logger.info(f"Successfully updated {table}: {column} = {value} WHERE {condition}")
        return {"status": "success", "message": f"Updated {table}"}

    except HTTPException as e:
        # Log client-side errors
        api_logger.warning(f"Client error: {str(e)}")
        raise e

    except Exception as e:
        # Log server-side errors
        api_logger.error(f"Error updating {table}: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")
