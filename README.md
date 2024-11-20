# Problem Statement
Create a backend system that supports a shared spreadsheet-like application using DuckDB as the storage engine. The backend must handle: 
-Multi-user updates in real time. 
-Efficient data querying, aggregation, and modification. 
-Concurrency management for a single read/write connection to DuckDB.

# Overview
The following steps make up the backend design:
1. DuckDB: Single read-write connection using a singleton pattern
2. Real-time request-response: APIs with redis stream for multi-user communication
3. Analytical queries: Using joins, pivot, unpivot, union, group_by, grouping_sets, Windowing Functions, CTEs
4. Testing: Postman for testing and validation

# Key Modules
1. Python: To manage the DuckDB database
2. DuckDB manager: Implement singleton pattern to manage a single DuckDB connection
3. Redis: request_duck for incoming user requests, response_duck for sending responses back to users
4. Flask APIs: endpoints for CRUD operations and analytical queries, interfaces with DuckDB
5. Test Data: faker library to create real time test data

# Data Flow
1. API Interaction:
  - Request is received at 'POST/update_cell' end point in the FastAPI backend
  - Backend validates the request like is it a valid table, column, may be any condition that 
    is valid or not
  - The validated request is added to 'request_duck' stream
    Sample entry json:

    {
     "data": {
       "table": "table_name",
       "column": "column_name",
       "value": "some value",
       "condition": "condition"
     }
   }

2. Redis to DuckDB:
   - Create a python file that access the 'request_duck' stream and making sure the request is 
     retrieved and processed.
   - Singleton manager connects to the duckdb file and executes the sql.
     As in above json file, sql would be
     UPDATE table
     SET column = value
     where (conditions)
   - This triggers the parent-child relation in the view and is recalculated with grouping_sets
   - After the update, backend pushes the updated data to response_duck
  
3. Receiving updates:
   - sending a GET/get_updates request to access the updates
     Json sample output:
     {
     "data":{
       "updates":[
        {
         "brand":
         "family": 
           etc
        }
     }
   }

# Step-by-step process:
1. Set up environment
   -Install tools Python, Redis, DuckDB.
   -Start Redis server, set up DuckDB Database
2. Backend with FastAPI
   - Create a file for APIs to interact with Redis and DuckDB
3. Redis for communication
   - Create a python script for processing updates from Redis to DuckDB
4. Testing APIs
   - POST/update_cell: sends an update request to Redis request_duck
   - GET/get_updates: receives updates from redis response_duck
   - GET/view_table/{table_name}: gives full data of the table--considering this option
   
# Test cases
1.  Update a cell and validate the corresponding changes in DuckDB and Redis.
2.	Simulate multiple users sending updates simultaneously and validate that Redis and DuckDB handle updates sequentially(different cell/tables)
3.	Two users update the same cell simultaneously..is it expected to overwrite the first update? it manages the que..clarification needed.
4.	Update a parent node (Brand X) and verify proportional updates to child nodes.
5.	Update a parent node with zeroed child nodes and verify equal distribution.
6.	Update the sales table and ensure sales_summary_by_product_family view is consistent
7.	Update a non existent table/cell

	

