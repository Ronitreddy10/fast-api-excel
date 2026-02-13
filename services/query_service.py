"""
SQL Query Service - READ-ONLY SELECT queries only!

IMPORTANT: This module ONLY executes SELECT queries.
NEVER modify data - this is a production database!
"""
import pandas as pd
from typing import Optional, List, Dict, Any, Tuple
from datetime import date
from database import db, DatabaseError
from config import settings


class QueryService:
    """
    Service for executing read-only SQL queries.
    All queries use parameterized values to prevent SQL injection.
    """
    
    def __init__(self):
        self.max_rows = settings.MAX_ROWS
    
    def get_student_responses(
        self,
        contest_id: int,
        test_date: date,
        grade: Optional[int] = None,
        school_id: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch student responses for a contest on a specific test date.
        Returns a DataFrame with one row per student-question combination.
        
        This query will be pivoted later to have one row per student.
        """
        # Build the base query with all necessary joins
        # TOP clause is optional - 0 means no limit
        top_clause = f"TOP {self.max_rows}" if self.max_rows > 0 else ""
        query = f"""
        SELECT {top_clause}
            -- Test Date
            COALESCE(ts.TestStartDateTime, cc.ExamStartDateTime) AS TestDate,
            
            -- School Info
            s.Id AS SchoolId,
            s.SchoolName,
            
            -- Student Info
            u.LoginId AS StudentId,
            u.FirstName,
            u.LastName,
            u.Gender,
            u.Grade,
            
            -- Region (from School.RegionID -> Region table)
            COALESCE(reg.RegionName, 'N/A') AS Region,
            
            -- Question Info
            tr.QuestionID,
            COALESCE(qb.QuestionType, 'N/A') AS QuestionType,
            COALESCE(subj.SubjectName, 'N/A') AS Subject,
            COALESCE(lvl.LovName, 'N/A') AS Level,
            
            -- Answers and Score (strip HTML from CorrectAnswer, mark unanswered)
            CASE 
                WHEN tr.UserAnswer IS NULL OR tr.UserAnswer = '' THEN 'Not Answered'
                ELSE tr.UserAnswer 
            END AS StudentAnswer,
            -- Strip <p> and </p> tags from Answer
            REPLACE(REPLACE(COALESCE(qb.Answer, 'N/A'), '<p>', ''), '</p>', '') AS CorrectAnswer,
            COALESCE(tr.Credits, 0) AS Score
            
        FROM CCTTestResults tr WITH (NOLOCK)
        
        -- Join to Users for student info
        INNER JOIN Users u WITH (NOLOCK)
            ON tr.UserID = u.UserId
            
        -- Join to School
        INNER JOIN School s WITH (NOLOCK)
            ON u.SchoolId = s.Id
            
        -- Join to ContestCreation for test metadata
        INNER JOIN ContestCreation cc WITH (NOLOCK)
            ON tr.ContestCreationID = cc.ContestCreationID
            
        -- Left join to test attendance for actual test date
        LEFT JOIN CCTTestStudents ts WITH (NOLOCK)
            ON tr.UserID = ts.UserId 
            AND tr.ContestCreationID = ts.ContestCreationId
            
        -- Join to QBankMaster for question details
        LEFT JOIN QBankMaster qb WITH (NOLOCK)
            ON tr.QuestionID = qb.QuestionID
            
        -- Join to Subject for subject name
        LEFT JOIN Subject subj WITH (NOLOCK)
            ON qb.SubjectId = subj.SubjectId
            
        -- Join to Lov for question difficulty level
        LEFT JOIN Lov lvl WITH (NOLOCK)
            ON qb.Level = lvl.LovId
            
        -- Join for Region from School.RegionID
        LEFT JOIN Region reg WITH (NOLOCK)
            ON s.RegionID = reg.RegionID
            
        WHERE tr.ContestCreationID = ?
        AND CAST(COALESCE(ts.TestStartDateTime, cc.ExamStartDateTime) AS DATE) = ?
        """
        
        # Build parameter list
        params: List[Any] = [contest_id, test_date.isoformat()]
        
        # Add optional filters
        if grade is not None:
            query += " AND u.Grade = ?"
            params.append(grade)
            
        if school_id is not None:
            query += " AND s.Id = ?"
            params.append(school_id)
        
        # Order by student and question
        query += """
        ORDER BY 
            s.SchoolName,
            u.LastName,
            u.FirstName,
            tr.QuestionID
        """
        
        # Execute query and return DataFrame
        try:
            with db.get_connection() as conn:
                df = pd.read_sql_query(query, conn, params=params)
                return df
        except Exception as e:
            raise DatabaseError(f"Error fetching student responses: {str(e)}")
    
    def get_contest_info(self, contest_id: int) -> Dict[str, Any]:
        """
        Get basic information about a contest.
        Useful for report headers and validation.
        """
        # Using only columns that are likely to exist
        query = """
        SELECT TOP 1
            cc.ContestCreationID,
            cc.ExamStartDateTime,
            cc.ExamEndDateTime
        FROM ContestCreation cc WITH (NOLOCK)
        WHERE cc.ContestCreationID = ?
        """
        
        try:
            with db.get_cursor() as cursor:
                cursor.execute(query, [contest_id])
                row = cursor.fetchone()
                if row:
                    columns = [column[0] for column in cursor.description]
                    return dict(zip(columns, row))
                return {}
        except Exception as e:
            raise DatabaseError(f"Error fetching contest info: {str(e)}")
    
    def get_question_count(self, contest_id: int) -> int:
        """
        Get the number of unique questions in a contest.
        Used for determining Excel column structure.
        """
        query = """
        SELECT COUNT(DISTINCT tr.QuestionID) AS QuestionCount
        FROM CCTTestResults tr WITH (NOLOCK)
        WHERE tr.ContestCreationID = ?
        """
        
        try:
            with db.get_cursor() as cursor:
                cursor.execute(query, [contest_id])
                row = cursor.fetchone()
                return row[0] if row else 0
        except Exception as e:
            raise DatabaseError(f"Error fetching question count: {str(e)}")
    
    def validate_contest_exists(self, contest_id: int) -> bool:
        """
        Check if a contest exists in the database.
        """
        query = """
        SELECT TOP 1 1
        FROM ContestCreation WITH (NOLOCK)
        WHERE ContestCreationID = ?
        """
        
        try:
            with db.get_cursor() as cursor:
                cursor.execute(query, [contest_id])
                return cursor.fetchone() is not None
        except Exception as e:
            raise DatabaseError(f"Error validating contest: {str(e)}")
    
    def get_available_test_dates(self, contest_id: int) -> List[str]:
        """
        Get all unique test dates for a contest.
        Returns a list of dates in YYYY-MM-DD format, sorted descending.
        """
        query = """
        SELECT DISTINCT 
            CAST(COALESCE(ts.TestStartDateTime, cc.ExamStartDateTime) AS DATE) AS TestDate
        FROM CCTTestResults tr WITH (NOLOCK)
        INNER JOIN ContestCreation cc WITH (NOLOCK)
            ON tr.ContestCreationID = cc.ContestCreationID
        LEFT JOIN CCTTestStudents ts WITH (NOLOCK)
            ON tr.UserID = ts.UserId 
            AND tr.ContestCreationID = ts.ContestCreationId
        WHERE tr.ContestCreationID = ?
        ORDER BY TestDate DESC
        """
        
        try:
            with db.get_cursor() as cursor:
                cursor.execute(query, [contest_id])
                rows = cursor.fetchall()
                return [row[0].strftime('%Y-%m-%d') if row[0] else None for row in rows if row[0]]
        except Exception as e:
            raise DatabaseError(f"Error fetching test dates: {str(e)}")


# Global service instance
query_service = QueryService()
