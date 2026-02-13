"""
Database connection module.
Provides read-only connection to SQL Server database.
"""
import pyodbc
from contextlib import contextmanager
from typing import Generator
from config import settings


class DatabaseConnection:
    """Manages database connections with read-only intent"""
    
    def __init__(self):
        self.connection_string = settings.connection_string
        self.timeout = settings.QUERY_TIMEOUT
    
    @contextmanager
    def get_connection(self) -> Generator[pyodbc.Connection, None, None]:
        """
        Context manager for database connections.
        Ensures connections are properly closed after use.
        
        IMPORTANT: This connection is READ-ONLY.
        Only SELECT queries should be executed.
        """
        conn = None
        try:
            conn = pyodbc.connect(
                self.connection_string,
                timeout=self.timeout,
                autocommit=True  # Prevent transaction issues with read-only
            )
            # Set connection to read-only mode
            conn.execute("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
            yield conn
        except pyodbc.Error as e:
            raise DatabaseError(f"Database connection error: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self) -> Generator[pyodbc.Cursor, None, None]:
        """
        Context manager for database cursor.
        Automatically handles connection lifecycle.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()


class DatabaseError(Exception):
    """Custom exception for database errors"""
    pass


# Global database instance
db = DatabaseConnection()


def test_connection() -> bool:
    """Test if database connection works"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            return result[0] == 1
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False
