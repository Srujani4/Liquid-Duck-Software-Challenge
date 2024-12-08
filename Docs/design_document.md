# Design Document for Real-Time Shared Spreadsheet Backend

## Table of Contents

1. [Introduction](#1-introduction)
   - [1.1 Purpose and Scope](#11-purpose-and-scope)
   - [1.2 Audience](#12-audience)
   - [1.3 Sources of Information](#13-sources-of-information)
2. [Current Process Overview](#2-current-process-overview)
   - [2.1 Current Challenges](#21-current-challenges)
   - [2.2 Objective of the Proposed System](#22-objective-of-the-proposed-system)
3. [Application Integration Requirements](#3-application-integration-requirements)
   - [3.1 Components in Scope](#31-components-in-scope)
   - [3.2 Supporting Components](#32-supporting-components)
4. [Solution Architecture](#4-solution-architecture)
   - [4.1 Architectural Diagram](#41-architectural-diagram)
   - [4.2 Data Flow for Update Process](#42-data-flow-for-update-process)
   - [4.3 Rebalancing Logic](#43-rebalancing-logic)
   - [4.4 Modules and Their Responsibilities](#44-modules-and-their-responsibilities)
5. [Information Security](#5-information-security)
   - [5.1 API Authentication](#51-api-authentication)
   - [5.2 Redis Security](#52-redis-security)
   - [5.3 Data Integrity in DuckDB](#53-data-integrity-in-duckdb)
6. [Technology Stack](#6-technology-stack)
   - [6.1 Software Components](#61-software-components)
7. [Application Capacity Planning](#7-application-capacity-planning)
   - [7.1 Scalability](#71-scalability)
   - [7.2 High-Availability Planning](#72-high-availability-planning)
8. [Dependencies](#8-dependencies)
9. [Assumptions](#9-assumptions)
10. [Test Cases](#10-test-cases)

---

## 1. Introduction

### 1.1 Purpose and Scope

This document outlines the design and implementation of a backend architecture for a real-time shared spreadsheet engine, supporting multi-user updates. The backend is powered by **DuckDB** for data storage, **Redis** for messaging, and **FastAPI** for API communication.

### 1.2 Audience

This document is intended for the **Liquid Analytics team**, development teams, and other stakeholders involved in the project.

### 1.3 Sources of Information

- Project requirements shared in the challenge document.
- Design patterns for Redis and DuckDB integrations.
- API best practices and real-time update systems.

---

## 2. Current Process Overview

### 2.1 Current Challenges

- Lack of a backend system that supports real-time updates.
- Inconsistent data aggregation in hierarchical structures.
- Difficulty in synchronizing updates across multiple users.

### 2.2 Objective of the Proposed System

- Enable multi-user collaboration on a shared spreadsheet.
- Maintain consistent parent-child relationships using rebalancing logic.
- Provide APIs for CRUD operations and real-time synchronization.

---

## 3. Application Integration Requirements

### 3.1 Components in Scope

| **Component** | **Integration Method** | **Description** |
| ------------- | ---------------------- | --------------- |
| **FastAPI**   | REST APIs              | APIs for user interactions |
| **Redis**     | Streams                | Message queuing and updates |
| **DuckDB**    | SQL Queries            | Stores and processes data |

### 3.2 Supporting Components

| **Component** | **Integration Method** | **Description** |
| ------------- | ---------------------- | --------------- |
| **Postman**   | REST API Testing       | Tests APIs for functionality |
| **Python**    | Library Support        | Implements Redis/DuckDB logic |

---

## 4. Solution Architecture

### 4.1 Architectural Diagram

Below is the architecture flowchart for the project:

![Architecture Flowchart](images/architecture_flowchart.png)

The flowchart illustrates interactions between users, APIs, Redis, DuckDB, and other components.

### 4.2 Data Flow for Update Process

1. **User Action:**
   - User sends a `POST /update_cell` request with details of the cell to be updated.

2. **Redis Stream:**
   - The request is queued in the `request_duck` stream.

3. **DuckDB Processing:**
   - Singleton Manager fetches the request, updates DuckDB, and recalculates affected views.

4. **Rebalancing:**
   - Proportional or equal distribution logic is applied.

5. **Redis Broadcast:**
   - Updated data is pushed to the `response_duck` stream.

6. **User Notification:**
   - Users fetch updates via `GET /get_updates`.

### 4.3 Rebalancing Logic

- **Proportional Distribution:** Adjust child values proportionally to match parent totals.
- **Equal Distribution:** Assigns equal values to children if all current values are zero.

```sql
WITH updated_children AS (
    SELECT child_id, value * (new_parent_value / SUM(value)) AS new_value
    FROM children
    WHERE parent_id = X
)
UPDATE children
SET value = new_value
WHERE child_id IN (SELECT child_id FROM updated_children);
```

### 4.4 Modules and Their Responsibilities

| **Module**                | **Responsibility**                                      |
| ------------------------- | ------------------------------------------------------- |
| **FastAPI**               | Exposes REST APIs for CRUD operations.                  |
| **Redis Streams**         | Handles real-time message queuing.                      |
| **DuckDB Singleton**      | Executes SQL queries and manages updates.               |
| **Rebalancing Module**    | Ensures data consistency in hierarchies.                |

---

## 5. Information Security

### 5.1 API Authentication

- Use API keys or OAuth tokens to secure endpoints.

### 5.2 Redis Security

- Use password protection and SSL for Redis communication.

### 5.3 Data Integrity in DuckDB

- Transactions ensure atomicity during updates.

---

## 6. Technology Stack

### 6.1 Software Components

- **Programming Language:** Python
- **API Framework:** FastAPI
- **Database:** DuckDB
- **Message Queue:** Redis

---

## 7. Application Capacity Planning

### 7.1 Scalability

- Redis cluster for handling high volumes of messages.
- Read-only replicas of DuckDB for load balancing.

### 7.2 High-Availability Planning

- Backup Redis streams and DuckDB snapshots for failover.

---

## 8. Dependencies

- **Redis server** for messaging.
- **DuckDB** for SQL processing.
- Python libraries: `fastapi`, `redis`, `duckdb`.

---

## 9. Assumptions

- Users interact with the backend via APIs or a frontend (to be developed later).
- Redis and DuckDB are hosted on the same server for low-latency communication.
- Proper indexing is implemented in DuckDB for query optimization.

---

## 10. Test Cases

1. Update a cell and validate the corresponding changes in DuckDB and Redis.
2. Simulate multiple users sending updates simultaneously and validate that Redis and DuckDB handle updates sequentially.
3. Update a parent node (e.g., Brand X) and verify proportional updates to child nodes.
4. Update a parent node with zeroed child nodes and verify equal distribution.
5. Update the sales table and ensure `sales_summary_by_product_family` view is consistent.
6. Attempt to update a non-existent table/cell and verify the response.

---

This version of the document is now more structured, with clearer explanations, formatted code blocks, and consistent usage of tables and lists. Each section is organized to make it easier for the reader to navigate and understand the design.
