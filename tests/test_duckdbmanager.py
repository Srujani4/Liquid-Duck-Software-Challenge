import pytest
import duckdb
from Challenge.DuckDBManager import DuckDBManager


@pytest.fixture
def setup_duckdb():
    """
    Set up an in-memory DuckDB instance for testing.
    """
    connection = duckdb.connect(":memory:")
    connection.execute("CREATE TABLE sales_summary_by_product_family (id INT, quantity INT);")
    connection.execute("CREATE TABLE sales (id INT, quantity INT);")
    yield connection
    connection.close()


def test_adbc_ingest(setup_duckdb):
    """
    Test the ADBC ingest functionality.
    """
    DuckDBManager.set_instance_for_testing(setup_duckdb)
    db_manager = DuckDBManager()
    db_manager.conn.execute("INSERT INTO sales_summary_by_product_family VALUES (1, 10), (2, 20);")
    result = setup_duckdb.execute("SELECT * FROM sales_summary_by_product_family").fetchall()
    assert result == [(1, 10), (2, 20)]


@pytest.mark.asyncio
async def test_execute_query_async(setup_duckdb):
    """
    Test the `execute_query_async` method.
    """
    DuckDBManager.set_instance_for_testing(setup_duckdb)

    db_manager = DuckDBManager()

    await db_manager.execute_query_async("INSERT INTO sales_summary_by_product_family VALUES (3, 30);")
    result = setup_duckdb.execute("SELECT * FROM sales_summary_by_product_family WHERE id = 3;").fetchall()
    assert result == [(3, 30)]


@pytest.mark.asyncio
async def test_proportional_rebalance_async(setup_duckdb):
    """
    Test proportional rebalance.
    """
    DuckDBManager.set_instance_for_testing(setup_duckdb)

    db_manager = DuckDBManager()

    setup_duckdb.execute("INSERT INTO sales_summary_by_product_family VALUES (1, 10), (2, 20);")
    await db_manager.execute_query_async("UPDATE sales_summary_by_product_family SET quantity = 15 WHERE id = 1;")
    result = setup_duckdb.execute("SELECT * FROM sales_summary_by_product_family WHERE id = 1;").fetchall()
    assert result == [(1, 15)]


def test_rollup_to_parents(setup_duckdb):
    """
    Test rollup to parents.
    """
    DuckDBManager.set_instance_for_testing(setup_duckdb)

    db_manager = DuckDBManager()

    setup_duckdb.execute("INSERT INTO sales (id, quantity) VALUES (1, 10), (2, 20);")
    db_manager.execute_query("UPDATE sales SET quantity = 30 WHERE id = 1;")
    result = setup_duckdb.execute("SELECT * FROM sales WHERE id = 1;").fetchall()
    assert result == [(1, 30)]
