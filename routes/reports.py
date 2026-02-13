"""
API routes for report generation.
"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, List
from datetime import date, datetime

from services.query_service import query_service
from services.excel_service import excel_service
from database import DatabaseError


router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/test-dates/{contest_id}")
async def get_test_dates(contest_id: int):
    """
    Get all available test dates for a contest.
    Use this to populate a date picker before downloading the report.
    """
    try:
        if not query_service.validate_contest_exists(contest_id):
            raise HTTPException(
                status_code=404,
                detail=f"Contest with ID {contest_id} not found"
            )
        
        dates = query_service.get_available_test_dates(contest_id)
        return {
            "contest_id": contest_id,
            "test_dates": dates,
            "total_dates": len(dates)
        }
        
    except DatabaseError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@router.get("/student-responses")
async def get_student_responses_report(
    contest_id: int = Query(..., description="Contest/Test ID (required)"),
    test_date: date = Query(..., description="Test date (YYYY-MM-DD) - required"),
    grade: Optional[int] = Query(None, description="Filter by grade level"),
    school_id: Optional[int] = Query(None, description="Filter by school ID")
):
    """
    Generate an Excel report of student responses for a contest.
    
    Returns an Excel file with:
    - Fixed student columns (TestDate, SchoolId, SchoolName, StudentId, etc.)
    - Dynamic question columns (Q1_QuestionId, Q1_Subject, Q1_Level, etc.)
    
    Each student appears as ONE row with all their question responses as columns.
    """
    try:
        # Validate contest exists
        if not query_service.validate_contest_exists(contest_id):
            raise HTTPException(
                status_code=404,
                detail=f"Contest with ID {contest_id} not found"
            )
        
        # Get contest info for the report header
        contest_info = query_service.get_contest_info(contest_id)
        
        # Fetch the student response data for the specific test date
        raw_df = query_service.get_student_responses(
            contest_id=contest_id,
            test_date=test_date,
            grade=grade,
            school_id=school_id
        )
        
        # Pivot the data to one row per student
        pivoted_df = excel_service.pivot_student_data(raw_df)
        
        # Generate the Excel file
        excel_buffer = excel_service.generate_excel(
            df=pivoted_df,
            contest_id=contest_id,
            contest_info=contest_info
        )
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"student_responses_contest_{contest_id}_{timestamp}.xlsx"
        
        # Return as downloadable file
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except DatabaseError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating report: {str(e)}"
        )


@router.get("/contest-info/{contest_id}")
async def get_contest_info(contest_id: int):
    """
    Get information about a specific contest.
    Useful for validating contest IDs and getting metadata.
    """
    try:
        if not query_service.validate_contest_exists(contest_id):
            raise HTTPException(
                status_code=404,
                detail=f"Contest with ID {contest_id} not found"
            )
        
        info = query_service.get_contest_info(contest_id)
        question_count = query_service.get_question_count(contest_id)
        
        return {
            "contest_id": contest_id,
            "contest_info": info,
            "question_count": question_count
        }
        
    except DatabaseError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
