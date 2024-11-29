import duckdb
import pandas as pd
import random
from faker import Faker

# Initialize Faker
fake = Faker()

# Connect to DuckDB
conn = duckdb.connect("sales_metrics.duckdb")


conn.execute("DROP TABLE IF EXISTS product")


# 1. Create Product Table
product_data = pd.DataFrame(
    {
        "product_id": range(1, 6),
        "name": [f"{fake.word()} {fake.color_name()} Soda" for _ in range(5)],
        "supplier": [fake.company() for _ in range(5)],
        "brand": [fake.word() for _ in range(5)],
        "family": [fake.word() for _ in range(5)],
    }
)
conn.execute("CREATE TABLE product AS SELECT * FROM product_data")

conn.execute("DROP TABLE IF EXISTS customer")

# 2. Create Customer Table
customer_data = pd.DataFrame(
    {
        "customer_id": range(1, 6),
        "type": [
            fake.random_element(elements=("Restaurant", "Bar", "GroceryStore"))
            for _ in range(5)
        ],
        "capacity": [fake.random_int(min=10, max=100) for _ in range(5)],
        "chain": [fake.company() for _ in range(5)],
        "city": [fake.city() for _ in range(5)],
        "province": [fake.state_abbr() for _ in range(5)],
        "postal_code": [fake.postcode() for _ in range(5)],
    }
)
conn.execute("CREATE TABLE customer AS SELECT * FROM customer_data")

conn.execute("DROP TABLE IF EXISTS sales")

# 3. Create Sales Table
sales_data = pd.DataFrame(
    {
        "product_id": [fake.random_int(min=1, max=5) for _ in range(10)],
        "customer_id": [fake.random_int(min=1, max=5) for _ in range(10)],
        "invoice_date": [fake.date_this_year().strftime
                         ("%Y-%m-%d") for _ in range(10)],
        "quantity": [fake.random_int(min=1, max=50) for _ in range(10)],
        # "net_price": [fake.random_float(min=10.0, max=100.0,
        # ndigits=2) for _ in range(10)]
        "net_price": [round(random.uniform(10.0, 100.0), 2)
                      for _ in range(10)],
    }
)
conn.execute("CREATE TABLE sales AS SELECT * FROM sales_data")

print("Created tables: product, customer, sales")

tables = ["product", "customer", "sales"]

# Loop through the tables and print their contents
for table in tables:
    print(f"Contents of table: {table}")
    result = conn.execute(f"SELECT * FROM {table};").fetchdf()  # DataFrame
    print(result)
    print("-" * 50)  # Separator for better readability

conn.execute("DROP TABLE IF EXISTS sales_summary_by_product_family")

conn.execute(
    """
    CREATE TABLE sales_summary_by_product_family AS
    SELECT
        p.supplier,
        p.brand,
        p.family,
        STRFTIME(CAST(s.invoice_date AS DATE), '%Y-%m') AS invoice_date_month,
        SUM(s.quantity) AS quantity,
        SUM(s.net_price) AS net_amount,
        GROUPING_ID(p.supplier, p.brand, p.family) AS grouping_set_id
    FROM sales s
    JOIN product p ON s.product_id = p.product_id
    GROUP BY GROUPING SETS (
        (p.supplier, p.brand, p.family, STRFTIME(CAST(s.invoice_date AS
        DATE), '%Y-%m')),
        (p.supplier, p.brand, STRFTIME(CAST(s.invoice_date AS DATE), '%Y-%m')),
        (p.supplier, STRFTIME(CAST(s.invoice_date AS DATE), '%Y-%m'))
    );
"""
)
print("Created denormalized table: sales_summary_by_product_family")


tables = ["sales_summary_by_product_family"]

# print contents
for table in tables:
    print(f"Contents of table: {table}")
    result = conn.execute(f"SELECT * FROM {table};").fetchdf()  # DataFrame
    print(result)
    print("-" * 50)  

conn.execute("DROP VIEW IF EXISTS pivoted_sales")

# Pivot: columns are invoice months
conn.execute(
    """
    CREATE VIEW pivoted_sales AS
    SELECT *
    FROM (
        SELECT supplier, brand, family, invoice_date_month, quantity
        FROM sales_summary_by_product_family
    )
    PIVOT (
        SUM(quantity) FOR invoice_date_month IN ('2024-01', '2024-02',
        '2024-03', '2024-04')
    );
"""
)
print("Created pivoted view: pivoted_sales")

conn.execute("DROP VIEW IF EXISTS unpivoted_sales")

# Unpivot: Transform columns back into rows
conn.execute(
    """
    CREATE VIEW unpivoted_sales AS
    SELECT supplier, brand, family, month_column AS invoice_date_month,
    quantity
    FROM pivoted_sales
    UNPIVOT (
        quantity FOR month_column IN ('2024-01', '2024-02', '2024-03',
        '2024-04')
    );
"""
)
print("Created unpivoted view: unpivoted_sales")

# Query Pivoted View
pivoted_df = conn.execute("SELECT * FROM pivoted_sales").fetchdf()
print("Pivoted Sales View:")
print(pivoted_df)

# Query Unpivoted View
unpivoted_df = conn.execute("SELECT * FROM unpivoted_sales").fetchdf()
print("\nUnpivoted Sales View:")
print(unpivoted_df)

conn.commit()
