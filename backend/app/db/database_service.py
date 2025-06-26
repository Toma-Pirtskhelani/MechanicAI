from supabase import create_client, Client
from typing import List, Dict, Any, Optional
import logging
from app.config import config

logger = logging.getLogger(__name__)


class DatabaseService:
    """Database service for Supabase operations"""
    
    def __init__(self):
        """Initialize Supabase client"""
        self.client: Client = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_KEY
        )
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check database health and return status with available tables
        
        Returns:
            Dict containing status and list of tables
        """
        try:
            # Test connection by getting tables
            tables = self.get_tables()
            
            return {
                "status": "healthy",
                "tables": tables,
                "connection": "successful"
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection": "failed"
            }
    
    def get_tables(self) -> List[str]:
        """
        Get list of tables in the database
        
        Returns:
            List of table names
        """
        try:
            # Try to query each expected table to check if it exists
            expected_tables = ["conversations", "messages", "conversation_contexts"]
            existing_tables = []
            
            for table in expected_tables:
                try:
                    # Try to query the table with limit 0 to check if it exists
                    self.client.table(table).select("*").limit(0).execute()
                    existing_tables.append(table)
                except Exception as e:
                    logger.debug(f"Table {table} not accessible: {e}")
                    # Table doesn't exist or can't be accessed
                    pass
            
            return existing_tables
            
        except Exception as e:
            logger.error(f"Error getting tables: {e}")
            return []
    
    def perform_basic_query_test(self) -> Optional[Dict[str, Any]]:
        """
        Perform a basic database operation test using Supabase table API
        
        Returns:
            Dict with test results, or None if error
        """
        try:
            # Test basic database connectivity by querying conversations table structure
            # This is a real operation that tests the actual database connection
            result = self.client.table('conversations').select("*").limit(1).execute()
            
            if hasattr(result, 'data'):
                return {
                    "test_passed": True,
                    "table_accessible": True,
                    "query_successful": True,
                    "row_count": len(result.data) if result.data else 0
                }
            
            return None
                
        except Exception as e:
            logger.error(f"Error performing basic query test: {e}")
            return {
                "test_passed": False,
                "error": str(e),
                "table_accessible": False
            }
    
    def test_connection(self) -> bool:
        """
        Test if database connection is working
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to execute a simple operation
            result = self.client.table('conversations').select("count", count="exact").limit(0).execute()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def test_crud_operations(self) -> Dict[str, Any]:
        """
        Test basic CRUD operations to verify database functionality
        
        Returns:
            Dict with test results for each operation
        """
        test_results = {
            "create": False,
            "read": False,
            "delete": False,
            "error": None
        }
        
        test_conversation_id = None
        
        try:
            # Test CREATE - Insert a test conversation
            test_data = {
                "user_id": "test_user_db_connection",
                "language": "en",
                "title": "Database Connection Test",
                "status": "active"
            }
            
            create_result = self.client.table('conversations').insert(test_data).execute()
            
            if hasattr(create_result, 'data') and create_result.data:
                test_conversation_id = create_result.data[0]['id']
                test_results["create"] = True
                logger.info(f"Created test conversation: {test_conversation_id}")
            
            # Test READ - Retrieve the test conversation
            if test_conversation_id:
                read_result = self.client.table('conversations').select("*").eq('id', test_conversation_id).execute()
                
                if hasattr(read_result, 'data') and read_result.data:
                    retrieved_conversation = read_result.data[0]
                    if retrieved_conversation['user_id'] == "test_user_db_connection":
                        test_results["read"] = True
                        logger.info("Successfully read test conversation")
            
            # Test DELETE - Clean up the test conversation
            if test_conversation_id:
                delete_result = self.client.table('conversations').delete().eq('id', test_conversation_id).execute()
                test_results["delete"] = True
                logger.info("Successfully deleted test conversation")
                
        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"CRUD test failed: {e}")
            
            # Cleanup attempt if something went wrong
            if test_conversation_id:
                try:
                    self.client.table('conversations').delete().eq('id', test_conversation_id).execute()
                except:
                    pass  # Cleanup failed, but that's okay for a test
        
        return test_results 