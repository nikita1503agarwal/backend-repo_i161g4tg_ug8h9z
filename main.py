import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import Course, Lesson, Enrollment

app = FastAPI(title="E-learning API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CourseResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    level: str
    author: str
    thumbnail_url: Optional[str] = None
    tags: List[str] = []
    is_premium: bool
    is_free_access: bool

class LessonResponse(BaseModel):
    id: str
    course_id: str
    title: str
    content: Optional[str] = None
    video_url: Optional[str] = None
    order: int

@app.get("/")
def read_root():
    return {"message": "E-learning Backend is running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# Helper: convert Mongo document to response dict

def to_course_response(doc) -> CourseResponse:
    return CourseResponse(
        id=str(doc.get("_id")),
        title=doc.get("title"),
        description=doc.get("description"),
        category=doc.get("category"),
        level=doc.get("level"),
        author=doc.get("author"),
        thumbnail_url=doc.get("thumbnail_url"),
        tags=doc.get("tags", []),
        is_premium=doc.get("is_premium", False),
        is_free_access=doc.get("is_free_access", True)
    )


def to_lesson_response(doc) -> LessonResponse:
    return LessonResponse(
        id=str(doc.get("_id")),
        course_id=str(doc.get("course_id")),
        title=doc.get("title"),
        content=doc.get("content"),
        video_url=doc.get("video_url"),
        order=doc.get("order", 1)
    )

# API: Courses

@app.post("/api/courses", response_model=dict)
def create_course(course: Course):
    try:
        inserted_id = create_document("course", course)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/courses", response_model=List[CourseResponse])
def list_courses(category: Optional[str] = None, search: Optional[str] = None):
    try:
        filter_dict = {}
        if category:
            filter_dict["category"] = category
        if search:
            # Simple text search across title and description
            filter_dict["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        docs = get_documents("course", filter_dict=filter_dict)
        return [to_course_response(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# API: Lessons

@app.post("/api/lessons", response_model=dict)
def create_lesson(lesson: Lesson):
    try:
        # Ensure referenced course exists
        if not ObjectId.is_valid(lesson.course_id):
            raise HTTPException(status_code=400, detail="Invalid course_id")
        course = db["course"].find_one({"_id": ObjectId(lesson.course_id)})
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        inserted_id = create_document("lesson", lesson)
        return {"id": inserted_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/courses/{course_id}/lessons", response_model=List[LessonResponse])
def list_lessons(course_id: str):
    try:
        if not ObjectId.is_valid(course_id):
            raise HTTPException(status_code=400, detail="Invalid course_id")
        docs = get_documents("lesson", {"course_id": course_id})
        return [to_lesson_response(d) for d in docs]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# API: Enrollments (free access)

@app.post("/api/enroll", response_model=dict)
def enroll(enrollment: Enrollment):
    try:
        if not ObjectId.is_valid(enrollment.course_id):
            raise HTTPException(status_code=400, detail="Invalid course_id")
        course = db["course"].find_one({"_id": ObjectId(enrollment.course_id)})
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        inserted_id = create_document("enrollment", enrollment)
        return {"id": inserted_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Simple seed endpoint to add sample courses quickly (optional helper)
@app.post("/api/seed")
def seed_data():
    try:
        samples = [
            {
                "title": "Python for Beginners",
                "description": "Start coding with Python from scratch. Hands-on exercises included.",
                "category": "Programming",
                "level": "Beginner",
                "author": "Jane Doe",
                "thumbnail_url": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4",
                "tags": ["python", "basics"],
                "is_premium": True,
                "is_free_access": True,
            },
            {
                "title": "UI Design Fundamentals",
                "description": "Learn color, typography, and layout to design beautiful interfaces.",
                "category": "Design",
                "level": "Beginner",
                "author": "John Smith",
                "thumbnail_url": "https://images.unsplash.com/photo-1523246191871-2c65d1d9d43a",
                "tags": ["ui", "design"],
                "is_premium": True,
                "is_free_access": True,
            },
        ]
        ids = []
        for s in samples:
            ids.append(str(db["course"].insert_one({**s}).inserted_id))
        return {"inserted": ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
