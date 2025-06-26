import pytest
from app.db.database_service import DatabaseService


def test_supabase_connection():
    """Test that we can connect to Supabase"""
    db = DatabaseService()
    health = db.health_check()
    assert health["status"] == "healthy"
    assert "tables" in health
    expected_tables = ["conversations", "messages", "conversation_contexts"]
    for table in expected_tables:
        assert table in health["tables"]


def test_database_service_initialization():
    """Test that DatabaseService initializes correctly"""
    db = DatabaseService()
    assert db.client is not None
    assert hasattr(db, 'health_check')


def test_supabase_credentials_loaded():
    """Test that Supabase credentials are properly loaded"""
    from app.config import Config
    assert Config.SUPABASE_URL is not None
    assert Config.SUPABASE_KEY is not None
    assert Config.SUPABASE_URL.startswith("https://")


def test_database_basic_operations():
    """Test basic database operations work"""
    db = DatabaseService()
    
    # Test basic query functionality
    result = db.perform_basic_query_test()
    assert result is not None
    assert result["test_passed"] is True
    assert result["table_accessible"] is True
    assert result["query_successful"] is True


def test_database_tables_exist():
    """Test that all required tables exist in the database"""
    db = DatabaseService()
    
    # Get list of tables
    tables = db.get_tables()
    assert isinstance(tables, list)
    
    required_tables = ["conversations", "messages", "conversation_contexts"]
    for table in required_tables:
        assert table in tables, f"Required table '{table}' not found in database"


def test_database_crud_operations():
    """Test full CRUD operations on the database"""
    db = DatabaseService()
    
    # Test Create, Read, Delete operations
    crud_results = db.test_crud_operations()
    assert crud_results["create"] is True, f"Create failed: {crud_results.get('error')}"
    assert crud_results["read"] is True, f"Read failed: {crud_results.get('error')}"
    assert crud_results["delete"] is True, f"Delete failed: {crud_results.get('error')}"
    assert crud_results["error"] is None, f"CRUD operations had errors: {crud_results['error']}"


def test_database_error_handling():
    """Test that database service handles errors gracefully"""
    db = DatabaseService()
    
    # Test query to non-existent table should be handled gracefully
    try:
        result = db.client.table('nonexistent_table').select("*").limit(1).execute()
        # If it doesn't raise an exception, that's unexpected
        assert False, "Expected an exception for non-existent table"
    except Exception as e:
        # This is expected - should get an error for non-existent table
        assert "does not exist" in str(e) or "not found" in str(e).lower() 