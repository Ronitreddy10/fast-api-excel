"""
Pydantic models for request validation and response schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import date, datetime
from enum import Enum


class ReportFilters(BaseModel):
    """Query parameters for the student responses report"""
    contest_id: int = Field(..., description="Contest/Test ID (required)")
    grade: Optional[int] = Field(None, description="Filter by grade level")
    school_id: Optional[int] = Field(None, description="Filter by school ID")
    date_from: Optional[date] = Field(None, description="Start date filter (YYYY-MM-DD)")
    date_to: Optional[date] = Field(None, description="End date filter (YYYY-MM-DD)")


class StudentInfo(BaseModel):
    """Student information from the database"""
    user_id: int
    login_id: str
    first_name: str
    last_name: str
    gender: Optional[str] = None
    grade: Optional[int] = None
    school_id: int
    school_name: str
    region: Optional[str] = None
    test_date: Optional[datetime] = None


class QuestionResponse(BaseModel):
    """Individual question response data"""
    question_id: int
    question_number: int
    subject: Optional[str] = None
    level: Optional[str] = None
    question_type: Optional[str] = None
    student_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    score: Optional[float] = None


class StudentReportRow(BaseModel):
    """Combined student info with all question responses"""
    student: StudentInfo
    responses: List[QuestionResponse]


class ReportMetadata(BaseModel):
    """Metadata about the generated report"""
    contest_id: int
    total_students: int
    total_questions: int
    generated_at: datetime
    filters_applied: dict


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    error_code: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    database_connected: bool
    timestamp: datetime
