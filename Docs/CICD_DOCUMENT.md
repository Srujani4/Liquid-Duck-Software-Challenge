# CI/CD Process and Project Documentation  

## Project Overview  
This project implements a backend system simulating a shared spreadsheet-like application, powered by **FastAPI**, **DuckDB**, and **Redis**. The CI/CD pipeline ensures code quality, automates testing, and validates data integrity for a production-ready deployment.  

This document covers:  
- Coding implementation details  
- Tools used  
- Structured ticketing system  

---

## 1. Tools, Packages, and Libraries  

### Backend Development  
- **FastAPI**: Python-based web framework for creating APIs with built-in support for **Pydantic** models for data validation.  
- **Uvicorn**: ASGI server for running the FastAPI application; lightweight and production-ready.  
- **Visual Studio Code**: Development environment for coding, debugging, and testing.  

### Database and Data Management  
- **DuckDB**: In-memory analytics database for managing queries and data views.  
- **Redis**: Handles request and response streams.  
- **Pydantic**: Ensures data validation and integrity in API endpoints.  
- **Faker**: Generates synthetic data for testing and populating DuckDB tables.  

### Dependency Management  
- **Poetry**: Handles dependency installation and versioning via `pyproject.toml`. Preferred over `pip` for better dependency resolution and virtual environment isolation.  

### Code Quality and Formatting  
- **Pydantic**: Validates request and response data for clean API processing.  
- **Flake8**: Linter to enforce PEP 8 standards.  
- **Black**: Code formatter for consistent style.  
- **Ruff**: Fast linter and formatter, combining functionalities of Flake8 and Black.  

### Testing  
- **Pytest**: Executes unit tests for database operations, Redis streams, and API endpoints. Supports integration testing for end-to-end validation.  
- **Coverage.py**: Measures test coverage to ensure all code paths are validated.  

### CI/CD Automation  
- **GitHub Actions**: Automates linting, testing, and deployment workflows, triggered by every push and pull request.  

### Deployment Tools  
- **Uvicorn**: Deploys the application in production with multi-threading support for concurrent user requests.  

### Additional Tools  
- **Postman**: Used for manual testing of API endpoints, simulating user requests and validating server responses.  
- **Pre-commit Hooks**: Automates code quality checks (linting, formatting) before committing changes.  

---

## 2. Coding Implementation  

### **File 1: `data.py` (Data Creation)**  
**Purpose**: Create and populate DuckDB tables (e.g., `product`, `customer`, `sales`).  
**Key Features**:  
- Generates synthetic data using `Faker`.  
- Creates a `sales_summary_by_product_family` table with grouping sets.  
- Implements pivot and unpivot views for data transformation.  

### **File 2: `DuckDBManager.py`**  
**Purpose**: Manage DuckDB operations.  
**Key Features**:  
- Implements a singleton class for a single read-write connection.  
- Methods for proportional rebalance, dependency updates, and recalculating summaries.  

### **File 3: `logger.py`**  
**Purpose**: Centralized logging for API, Redis, and database operations.  
**Key Features**:  
- Logs API requests, Redis interactions, and DuckDB queries.  
- Ensures logs are written to separate files for better tracking.  

### **File 4: `mainapi.py`**  
**Purpose**: Contains FastAPI routes for handling cell updates.  
**Key Features**:  
- Processes `/update_cell` API requests.  
- Validates input using Pydantic models.  
- Updates DuckDB tables and manages Redis request/response streams.  

### **File 5: `redislistener.py`**  
**Purpose**: Listens to Redis streams for processing requests and broadcasting updates.  
**Key Features**:  
- Reads from the `request_duck` stream.  
- Writes responses to the `response_duck` stream.  

---

## 3. CI/CD Pipeline Workflow  

### Step 1: Dependency Management  
1. Use `Poetry` for dependency management.  
   - Install dependencies: `poetry install`.  
   - Dependencies managed via `pyproject.toml` ensure consistent environments and simplify version upgrades.  

### Step 2: Linting and Formatting  
1. Use `Ruff` for faster linting: `ruff check app`.  
   - Combines linting (Flake8) and formatting (Black).  
   - Ideal for large codebases.    

### Step 3: Testing  
1. Write test cases using `Pytest`.  
2. Run tests: `pytest`.  
3. Measure coverage using `pytest-cov`: `pytest --cov=app`.  

### Step 4: GitHub Actions Configuration  
1. Automate the CI/CD pipeline with a workflow triggered on every push and pull request.  
   - Steps:  
     - Checkout code.  
     - Install dependencies via Poetry.  
     - Lint codebase with Ruff and Flake8.  
     - Run tests using Pytest.  

---

## Conclusion  
This documentation provides an end-to-end understanding of the project setup, coding practices, and CI/CD pipeline. By leveraging modern tools like Poetry, Ruff, and GitHub Actions, the project ensures high code quality, maintainability, and production-readiness.  
