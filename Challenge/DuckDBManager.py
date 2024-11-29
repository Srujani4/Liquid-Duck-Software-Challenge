import pyarrow
from adbc_driver_manager import dbapi
import threading
import asyncio


class DuckDBManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """
        Singleton Pattern: Ensure only one instance of DuckDBManager exists.
        """
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    # Modify the path and entrypoint for ADBC connection
                    cls._instance = super(DuckDBManager, cls).__new__(cls)
                    cls._instance.conn = dbapi.connect(
                        driver="C:/Users/svatt/libduckdb-windows-amd64/duckdb.dll",
                        entrypoint="duckdb_adbc_init",
                        db_kwargs={"path": "sales_metrics.duckdb"}
                    )
        return cls._instance

    def execute_query(self, query, params=None):
        """
        Synchronous query execution returning PyArrow table.
        """
        try:
            with self.conn.cursor() as cursor:
                print(f"Executing query: {query}")  
                cursor.execute(query, params or [])
                self.conn.commit()  
                print("Query executed successfully.")  
                return cursor.fetch_arrow_table()  # Return PyArrow table
        except Exception as e:
            print(f"Error during query execution: {e}")  
            raise

    async def execute_query_async(self, query, params=None):
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.execute_query,
                                              query, params)
        except Exception as e:
            print(f"Error during async query execution: {e}")  
            raise

    def adbc_ingest(self, table_name, arrow_table):
        """
        Ingest data into a DuckDB table using ADBC.
        """
        with self.conn.cursor() as cursor:
            cursor.adbc_ingest(table_name, arrow_table)

    def update_dependencies(self, table, column, value, condition):
        """
        Handle inter-table dependencies explicitly.
        """
        if table == "product":
            self.execute_query(
                f"""
                UPDATE sales
                SET {column} = '{value}'
                WHERE {condition};
            """
            )
            self.recalculate_summary()

    def recalculate_summary(self):
        """
        Recalculate the sales_summary_by_product_family table.
        """
        self.execute_query(
            """
            DELETE FROM sales_summary_by_product_family;
            INSERT INTO sales_summary_by_product_family
            SELECT
                p.supplier,
                p.brand,
                p.family,
                STRFTIME(CAST(s.invoice_date AS DATE), '%Y-%m') AS
                invoice_date_month,
                SUM(s.quantity) AS quantity,
                SUM(s.net_price) AS net_amount,
                GROUPING_ID(p.supplier, p.brand, p.family) AS grouping_set_id
            FROM sales s
            JOIN product p ON s.product_id = p.product_id
            GROUP BY GROUPING SETS (
                (p.supplier, p.brand, p.family, STRFTIME(CAST(s.invoice_date
                AS DATE), '%Y-%m')),
                (p.supplier, p.brand, STRFTIME(CAST(s.invoice_date AS DATE),
                '%Y-%m')),
                (p.supplier, STRFTIME(CAST(s.invoice_date AS DATE), '%Y-%m'))
            );
        """
        )

    def proportional_rebalance(self, level, supplier, brand, family,
                               new_value):
        """
        Rebalance child values proportionally based on a new parent value.
        """
        # Fetch current child values
        children = self.execute_query(
            f"""
            SELECT grouping_set_id, quantity
            FROM sales_summary_by_product_family
            WHERE grouping_set_id > {level} -- Only fetch child levels
            AND supplier = '{supplier}'
            AND brand = '{brand}'
            AND family = '{family}';
            """
        )

        total_quantity = sum(child[1] for child in children)
        for child_level, child_quantity in children:
            proportion = child_quantity/total_quantity if total_quantity else 1/len(children)
            new_child_value = new_value * proportion

            # Update child quantities
            self.execute_query(
                f"""
                UPDATE sales_summary_by_product_family
                SET quantity = {new_child_value}
                WHERE grouping_set_id = {child_level}
                AND supplier = '{supplier}'
                AND brand = '{brand}'
                AND family = '{family}';
                """
            )

    async def proportional_rebalance_async(self, level, new_value):
        """
        Asynchronously rebalance children proportionally on new parent value.
        """
        try:
            loop = asyncio.get_event_loop()
            
            # Fetch current child values
            children = await loop.run_in_executor(
                None,
                self.execute_query,
                f"""
                SELECT grouping_set_id, quantity
                FROM sales_summary_by_product_family
                WHERE grouping_set_id > {level};
                """
            )

            # Convert PyArrow scalars to native Python types
            children = [(child[0].as_py() if hasattr(child[0], "as_py") else child[0],
                        child[1].as_py() if hasattr(child[1], "as_py") else child[1])
                        for child in children]

            total_quantity = sum(child[1] for child in children)
            tasks = []
            for child_level, child_quantity in children:
                proportion = (
                    child_quantity / total_quantity if total_quantity else 1 / len(children)
                )
                new_child_value = new_value * proportion

                # Update child quantities asynchronously
                tasks.append(
                    loop.run_in_executor(
                        None,
                        self.execute_query,
                        f"""
                        UPDATE sales_summary_by_product_family
                        SET quantity = {new_child_value}
                        WHERE grouping_set_id = {child_level};
                        """
                    )
                )
              
            # Wait for all updates to complete
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"Error during proportional rebalance: {e}")
            raise

    def rollup_to_parents(self, level):
        # """
        # Rollup changes from a given level to higher levels.
        # Aggregates `quantity` and `net_amount` to the next higher level.
        # """
        self.execute_query(
            f"""
            UPDATE sales_summary_by_product_family
            SET quantity = (
                SELECT SUM(quantity)
                FROM sales_summary_by_product_family AS child
                WHERE child.grouping_set_id < {level} -- Rollup
                from lower levels
                AND child.supplier = sales_summary_by_product_family.supplier
                AND child.brand = sales_summary_by_product_family.brand
                AND child.family = sales_summary_by_product_family.family
            ),
            net_amount = (
                SELECT SUM(net_amount)
                FROM sales_summary_by_product_family AS child
                WHERE child.grouping_set_id < {level}
                AND child.supplier = sales_summary_by_product_family.supplier
                AND child.brand = sales_summary_by_product_family.brand
                AND child.family = sales_summary_by_product_family.family
            )
            WHERE grouping_set_id = {level};
            """
        )

    def equal_rebalance(self, level, supplier, brand, family, new_value):
        """
        Rebalance children equally if all child values are zero.
        """
        children = self.execute_query(
            f"""
            SELECT grouping_set_id
            FROM sales_summary_by_product_family
            WHERE grouping_set_id > {level}
            AND supplier = '{supplier}'
            AND brand = '{brand}'
            AND family = '{family}';
            """
        )

        equal_value = new_value / len(children)
        for child_level in children:
            self.execute_query(
                f"""
                UPDATE sales_summary_by_product_family
                SET quantity = {equal_value}
                WHERE grouping_set_id = {child_level}
                AND supplier = '{supplier}'
                AND brand = '{brand}'
                AND family = '{family}';
                """
            )


# Example
if __name__ == "__main__":
    db_manager = DuckDBManager()

    # Example: Ingest Data
    bands_data = pyarrow.table(
        {
            "Name": ["Tenacious D", "Backstreet Boys", "Wu Tang Clan"],
            "Albums": [4, 10, 7],
        }
    )
    db_manager.adbc_ingest("Bands", bands_data)

    # Example: Query Data
    result = db_manager.execute_query("SELECT * FROM Bands;")
    print(result.to_pandas())  # Convert PyArrow table to Pandas DataFrame

    # Example: Rollup
    db_manager.rollup_to_parents(1)

if __name__ == "__main__":
    db_manager = DuckDBManager()

    # Example: Direct Update
    db_manager.execute_query(
        """
        UPDATE sales_summary_by_product_family
        SET quantity = 500
        WHERE supplier = 'Smith Ltd '
        AND brand = 'many'
        AND family = 'impact';
        """
    )

    # Verify Update
    result = db_manager.execute_query("SELECT * FROM sales_summary_by_product_family;")
    print(result.to_pandas())
