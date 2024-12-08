# **Complete Execution Guide**

This guide provides a complete overview of setting up, executing, and testing the project. It includes steps for installing dependencies, running files, and testing the system via Postman.

---

## **1. Setup Environment**

### **1.1 Install Poetry**

If Poetry is not installed, use the following command:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Next, navigate to your project directory (e.g., `Liquid-Duck-Software-Challenge`) and initialize Poetry:

```bash
poetry init
```

The command will prompt you to:

- Set project name
- Define version
- Provide description
- Enter author(s) information
- Select license
- Specify Python version compatibility
- Add dependencies (optional during setup)

This will generate a `pyproject.toml` file in your project root.

Verify the installation with:

```bash
poetry --version
```

---

### **1.2 Clone the Repository**

Clone the project repository to your local machine:

```bash
git clone <your-repo-url>
cd <your-project-folder>
```

---

### **1.3 Configure Dependencies**

Install all project dependencies using Poetry. This will also create and activate a virtual environment for your project:

```bash
poetry install
```

Activate the Poetry shell:

```bash
poetry shell
```

---

### **1.4 Required Dependencies**

Here’s a list of the dependencies your project uses:

- **fastapi**: Framework for building APIs
- **uvicorn**: ASGI server to run FastAPI applications
- **duckdb**: Database engine for handling data
- **redis.asyncio**: Asynchronous Redis client for caching and streaming
- **pytest**, **pytest-asyncio**, **pytest-cov**: Testing libraries
- **pydantic**: For request validation
- **ruff**: Linting and code style enforcement

To install missing dependencies, run the following:

```bash
poetry add fastapi uvicorn duckdb redis.asyncio pydantic
```

For development dependencies:

```bash
poetry add --dev pytest pytest-asyncio pytest-cov ruff
```

---

## **2. Configure and Setup Files**

Ensure the following files exist in your project directory with the specified names:

- **data.py**: Manages schema definitions and data generation using Faker
- **logger.py**: Handles logging setup
- **DuckDBManager.py**: Manages DuckDB database connection and queries
- **mainapi.py**: Contains the FastAPI application with endpoints
- **tests/**: Contains unit tests for each file
- **pyproject.toml**: Contains Poetry configuration

---

## **3. Running Each File**

### **3.1 `logger.py`**

This file sets up logging for the project. Run it to ensure the logger is correctly configured:

```bash
poetry run python logger.py
```

### **3.2 `DuckDBManager.py`**

This file sets up and connects to the DuckDB database. Run it to verify the database connection:

```bash
poetry run python DuckDBManager.py
```

### **3.3 `data.py`**

This file generates sample data using Faker. Run it to populate the database:

```bash
poetry run python data.py
```

### **3.4 `mainapi.py`**

This is the main application file that starts the FastAPI server:

```bash
uvicorn mainapi:app --reload
```

The server should start successfully, and you will see:

```
INFO: Application startup complete.
INFO: Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### **3.5 Start Redis Server**

Ensure the Redis server is running on port 6379:

```bash
redis-server
```

To check updates manually:

```bash
redis-cli
XRANGE response_duck - +
```

---

## **4. Testing the API using Postman**

### **4.1 Start the Server**

Ensure `mainapi.py` is running on `http://127.0.0.1:8000`.

### **4.2 Add Endpoints in Postman**

#### 1. **Root Endpoint**

- **URL**: `http://127.0.0.1:8000/`
- **Method**: `GET`
- **Expected Response**:

```json
{
  "message": "Welcome!"
}
```

#### 2. **Update Cell**

- **URL**: `http://127.0.0.1:8000/update_cell`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Body Example**:

```json
{
  "table": "sales",
  "column": "quantity",
  "value": "50",
  "condition": "customer_id = 1 AND product_id = 1",
  "level": 0
}
```

- **Expected Response**:

```json
{
  "status": "success",
  "message": "Updated sales"
}
```

#### 3. **Get Updates**

- **URL**: `http://127.0.0.1:8000/get_updates`
- **Method**: `GET`
- **Expected Response**:

```json
{
  "status": "success",
  "updates": [
    {
      "table": "sales",
      "column": "quantity",
      "value": "50",
      "condition": "customer_id = 1 AND product_id = 1"
    }
  ]
}
```

**Check DuckDB for updated tables** in another terminal after stopping the server with `CTRL+C`.

```bash
duckdb
.salesmetrics.duckdb
.open tables
```

Execute the query for the table:

```sql
SELECT * FROM sales_summary_by_product_family WHERE condition;
```

---

## **5. Running Unit Tests**

Run the unit tests to verify the functionality:

```bash
pytest --cov=Challenge tests/
```

**Expected Output**:

- All test cases should pass.
- Coverage report should display a summary of test coverage.

---

## **6. CI/CD Setup (Yet to be done)**

Ensure you’ve configured `.github/workflows/python-app.yml` for GitHub Actions to automate tests, linting, and deployment. Push the changes to GitHub, and the workflow should trigger automatically.

---

## **Conclusion**

Following these steps, you can successfully set up, execute, and test the project from scratch.

---

This version enhances the readability of your documentation, ensuring that each section is clearly separated, and commands are highlighted properly using code blocks. Each action step is now more visually accessible and straightforward for users to follow.
