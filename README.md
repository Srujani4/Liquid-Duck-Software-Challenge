# **Backend System for a Shared Spreadsheet Application**

## **Problem Statement**
The objective is to develop a backend system that supports a shared spreadsheet-like application. This backend must facilitate multi-user updates in real time while ensuring efficient data querying, aggregation, and modification. Additionally, it must include robust concurrency management with a single read/write connection to DuckDB.

---

## **Overview**
The backend system is designed using a combination of modern technologies and tools to ensure high performance, scalability, and maintainability. The following components constitute the backend design:

1. **DuckDB**: A single read-write connection is implemented using the Singleton pattern.  
2. **Real-Time Request-Response**: Redis Streams facilitate multi-user communication and real-time updates.  
3. **Analytical Queries**: Advanced SQL features are utilized, including joins, pivot, unpivot, union, group by, grouping sets, windowing functions, and common table expressions (CTEs).  
4. **Testing**: Validation and testing are performed using Postman to ensure reliable functionality.

---

## **Key Modules**
The backend system comprises the following modules and components:

### **1. FastAPI**
Provides API endpoints for CRUD operations and analytical queries.

### **2. DuckDBManager**
Implements a Singleton Manager for handling DuckDB connections.

### **3. Redis**
Handles communication between user requests (`request_duck` stream) and responses (`response_duck` stream).

### **4. Python Scripts**
- **`data.py`**: Generates tables and test data using the `Faker` library.  
- **`mainapi.py`**: Main FastAPI application for managing API endpoints.  
- **`DuckDBManager.py`**: Implements the DuckDB Singleton Manager.  
- **`logger.py`**: Provides a centralized logging system.  

### **5. Documentation**
The `docs` folder contains:  
- Complete Execution Guide  
- Design Document  
- CI/CD Workflow Document  

---

## **Data Flow**

### **1. API Interaction**
A request is sent to the `POST/update_cell` endpoint in the FastAPI backend. The backend validates the request to ensure it refers to a valid table, column, or condition. After validation, the request is added to the `request_duck` stream in Redis in the following format:

```json
{
  "data": {
    "table": "table_name",
    "column": "column_name",
    "value": "some_value",
    "condition": "condition"
  }
}
```

### **2. Redis to DuckDB**
A Python script accesses the `request_duck` stream, retrieves the request, and processes it. The Singleton Manager establishes a connection with DuckDB and executes the corresponding SQL query. For example, the JSON above would result in the following SQL:

```sql
UPDATE table_name
SET column_name = some_value
WHERE condition;
```

This triggers updates in the view, recalculating parent-child relationships using `GROUPING SETS`. After processing, the updated data is pushed to the `response_duck` stream.

### **3. Receiving Updates**
Users can send a `GET/get_updates` request to retrieve the latest updates. The response format is as follows:

```json
{
  "data": {
    "updates": [
      {
        "brand": "value",
        "family": "value",
        ...
      }
    ]
  }
}
```

---

## **Step-by-Step Process**

### **1. Set Up the Environment**
- Install required tools: Python, Redis, and DuckDB.
- Start the Redis server and set up the DuckDB database.

### **2. Backend Development with FastAPI**
- Create API endpoints to interact with Redis and DuckDB.

### **3. Redis Communication**
- Implement a Python script to process updates from Redis to DuckDB.

### **4. Testing APIs**
- Use the following endpoints:
  - `POST/update_cell`: Sends an update request to `request_duck` in Redis.
  - `GET/get_updates`: Receives updates from `response_duck`.
  - `GET/view_table/{table_name}`: Retrieves the complete data for a specified table.

### **5. Execution Workflow**
1. Run `data.py` to create tables.
2. Establish a connection with DuckDB using the `DuckDBManager` Singleton class.
3. Use `logger.py` for centralized logging.
4. Launch the FastAPI app with Uvicorn to connect with Redis and DuckDB.
5. Use Postman to send requests and verify updates in Redis and DuckDB.

---

## **Test Cases**

### **1. Update Validation**
Update a cell and confirm the changes are reflected in DuckDB and Redis.

### **2. Multi-User Concurrency**
Simulate concurrent updates from multiple users using Redis Streams.

### **3. Parent-Child Updates**
Validate parent-to-child proportional updates in the data hierarchy.

### **4. Zeroed Child Nodes**
Distribute values equally among child nodes when parent nodes are zeroed.

### **5. Invalid Input Handling**
Ensure the system rejects invalid table or column names with appropriate error messages.


