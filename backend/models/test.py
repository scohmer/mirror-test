# Linux Mirror Testing Solution - Test Models

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TestRequest(BaseModel):
    """
    Request model for test configuration
    """
    distributions: List[str] = []
    repositories: List[str] = []
    timeout_seconds: Optional[int] = None
    parallel: bool = True

class TestResult(BaseModel):
    """
    Result model for individual test
    """
    id: str
    distribution: str
    repository: str
    status: str  # "success", "failure", "running"
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    package_count: Optional[int] = None
    test_details: Optional[dict] = None
