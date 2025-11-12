"""
Database Schemas for E-learning Platform

Each Pydantic model maps to a MongoDB collection with the lowercase class name:
- Course -> "course"
- Lesson -> "lesson"
- Enrollment -> "enrollment"

These are used for validation in API endpoints and by the database viewer.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List

class Course(BaseModel):
    """
    Courses collection schema
    Represents a course available on the platform
    Collection name: "course"
    """
    title: str = Field(..., min_length=3, max_length=120, description="Course title")
    description: str = Field(..., min_length=10, max_length=2000, description="Course description")
    category: str = Field(..., min_length=2, max_length=60, description="Course category e.g. Programming, Design")
    level: str = Field("Beginner", description="Level: Beginner, Intermediate, Advanced")
    author: str = Field(..., min_length=2, max_length=80, description="Instructor name")
    thumbnail_url: Optional[HttpUrl] = Field(None, description="Thumbnail image URL")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    is_premium: bool = Field(False, description="Originally premium/paid course")
    is_free_access: bool = Field(True, description="Provided free of cost on this platform")

class Lesson(BaseModel):
    """
    Lessons collection schema
    Represents a lesson within a course
    Collection name: "lesson"
    """
    course_id: str = Field(..., description="Related course _id as string")
    title: str = Field(..., min_length=3, max_length=160, description="Lesson title")
    content: Optional[str] = Field(None, description="Lesson content (markdown or text)")
    video_url: Optional[HttpUrl] = Field(None, description="Public video URL if available")
    order: int = Field(1, ge=1, description="Ordering within course")

class Enrollment(BaseModel):
    """
    Enrollments collection schema
    Tracks access for a learner to a course
    Collection name: "enrollment"
    """
    course_id: str = Field(..., description="Course _id as string")
    learner_name: Optional[str] = Field(None, max_length=80, description="Learner display name")
    email: Optional[str] = Field(None, max_length=120, description="Learner email")
