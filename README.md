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
1. FastAPI: Provides API endpoints for CRUD operations and analytical queries.
2. DuckDBManager: Singleton manager for handling DuckDB connections.
3. Redis: Handles incoming user requests (request_duck) and outgoing responses (response_duck).
4. Python Scripts:
	data.py: Generates tables and test data using the Faker library.
	mainapi.py: Main FastAPI application for managing API endpoints.
	DuckDBManager.py: Implements the DuckDB singleton manager.
	logger.py: Centralized logging system.
5. Documentation:(Docs folder)
	Complete Execution Guide
	Design Document
	CI/CD Workflow Document

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
  
# steps for execution
-Created and executed data.py to create tables
-Established a connection with DuckDB singleton class with DuckDBManager.py 
-Created centralised logs with logger.py file
-Ran the fast api with uvicorn to establish a connection with redis and duckdb thereby sending the requests through postman and updating the respective columns/tables.
-verified Redu=is cli for response updated and queried DuckDB to check the updates
   
# Test cases
1.Update a cell and validate the changes in DuckDB and Redis.
2.Simulate multi-user concurrent updates with Redis.
3.Parent-to-child proportional updates.
4.Equal distribution for zeroed child nodes.
5.Validation for invalid table/column inputs.

	

