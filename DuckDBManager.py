import adbc_driver_sqlite.dbapi as adbc
import threading

class DuckDBManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(DuckDBManager, cls).__new__(cls)
                    cls._instance.conn = adbc.connect("sales_metrics.duckdb")
        return cls._instance

    def execute_query(self, query, params=None):
        with self.conn.cursor() as cursor:
            cursor.execute(query, params or [])
            return cursor.fetchall()

    def update_dependencies(self, table, column, value, condition):
        """
        Handle inter-table dependencies explicitly.
        """
        if table == "product":
            # Update dependent sales table
            self.execute_query(f"""
                UPDATE sales
                SET {column} = '{value}'
                WHERE {condition};
            """)
            # Recalculate derived table
            self.recalculate_summary()

    def recalculate_summary(self):
        """
        Recalculate the sales_summary_by_product_family table.
        """
        self.execute_query("""
            DELETE FROM sales_summary_by_product_family;
            INSERT INTO sales_summary_by_product_family
            SELECT
                p.supplier,
                p.brand,
                p.family,
                STRFTIME(s.invoice_date, '%Y-%m') AS invoice_date_month,
                SUM(s.quantity) AS quantity,
                SUM(s.net_price) AS net_amount,
                GROUPING_ID(p.supplier, p.brand, p.family) AS grouping_set_id
            FROM sales s
            JOIN product p ON s.product_id = p.product_id
            GROUP BY GROUPING SETS ((p.supplier, p.brand, p.family), (p.supplier, p.brand), (p.supplier));
        """)

    def rollup_to_parents(self, parent_id):
        """
        Rollup changes to parent levels.
        """
        self.execute_query(f"""
            UPDATE sales_summary_by_product_family
            SET quantity = (
                SELECT SUM(quantity)
                FROM sales_summary_by_product_family
                WHERE parent_id = {parent_id}
            )
            WHERE node_id = {parent_id};
        """)

def proportional_rebalance(db_manager, parent_id, new_value):
    """
    Rebalance children proportionally based on current values.
    """
    children = db_manager.execute_query(f"""
        SELECT node_id, quantity
        FROM sales_summary_by_product_family
        WHERE parent_id = {parent_id};
    """)

    total_quantity = sum(child[1] for child in children)
    for child_id, child_quantity in children:
        proportion = child_quantity / total_quantity if total_quantity else 1 / len(children)
        new_child_value = new_value * proportion
        db_manager.execute_query(f"""
            UPDATE sales_summary_by_product_family
            SET quantity = {new_child_value}
            WHERE node_id = {child_id};
        """)

def equal_rebalance(db_manager, parent_id, new_value):
    """
    Rebalance children equally when all children are zero.
    """
    children = db_manager.execute_query(f"""
        SELECT node_id
        FROM sales_summary_by_product_family
        WHERE parent_id = {parent_id};
    """)

    equal_value = new_value / len(children)
    for child_id in children:
        db_manager.execute_query(f"""
            UPDATE sales_summary_by_product_family
            SET quantity = {equal_value}
            WHERE node_id = {child_id};
        """)
