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

#
