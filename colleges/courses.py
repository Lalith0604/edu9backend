import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from bson import ObjectId
from bson.errors import InvalidId

from .mongodb import colleges_collection, courses_collection


@csrf_exempt
def add_course(request):

    if request.method != "POST":
        return JsonResponse({
            "error": "Only POST requests are allowed"
        }, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON"
        }, status=400)

    required_fields = [
        "college_id",
        "course_name",
        "course_code",
        "degree",
        "duration_years",
        "total_seats",
        "tuition_fee",
        "eligibility",
        "admission_exam"
    ]

    for field in required_fields:

        if field not in data:
            return JsonResponse({
                "error": f"{field} is required"
            }, status=400)

    # Validate college ID
    try:
        college_id = ObjectId(data["college_id"])
    except InvalidId:
        return JsonResponse({
            "error": "Invalid college ID"
        }, status=400)

    # Check whether college exists
    college = colleges_collection.find_one({
        "_id": college_id
    })

    if college is None:
        return JsonResponse({
            "error": "College not found"
        }, status=404)

    # Prevent duplicate course code within the same college
    existing_course = courses_collection.find_one({
        "college_id": data["college_id"],
        "course_code": data["course_code"]
    })

    if existing_course:
        return JsonResponse({
            "error": "Course code already exists for this college"
        }, status=409)

    course = {
        "college_id": data["college_id"],
        "course_name": data["course_name"],
        "course_code": data["course_code"],
        "degree": data["degree"],
        "duration_years": data["duration_years"],
        "total_seats": data["total_seats"],
        "tuition_fee": data["tuition_fee"],
        "eligibility": data["eligibility"],
        "admission_exam": data["admission_exam"],
        "is_active": True
    }

    result = courses_collection.insert_one(course)

    return JsonResponse({
        "message": "Course added successfully",
        "course_id": str(result.inserted_id)
    }, status=201)

def get_college_courses(request, college_id):

    if request.method != "GET":
        return JsonResponse({
            "error": "Only GET requests are allowed"
        }, status=405)

    # Validate college ID
    try:
        object_id = ObjectId(college_id)
    except InvalidId:
        return JsonResponse({
            "error": "Invalid college ID"
        }, status=400)

    # Check whether college exists
    college = colleges_collection.find_one({
        "_id": object_id
    })

    if college is None:
        return JsonResponse({
            "error": "College not found"
        }, status=404)

    # Find courses belonging to this college
    courses = courses_collection.find({
        "college_id": college_id
    })

    results = []

    for course in courses:

        results.append({
            "id": str(course["_id"]),
            "college_id": course.get("college_id"),
            "course_name": course.get("course_name"),
            "course_code": course.get("course_code"),
            "degree": course.get("degree"),
            "duration_years": course.get("duration_years"),
            "total_seats": course.get("total_seats"),
            "tuition_fee": course.get("tuition_fee"),
            "eligibility": course.get("eligibility"),
            "admission_exam": course.get("admission_exam"),
            "is_active": course.get("is_active", True)
        })

    return JsonResponse({
        "college_id": college_id,
        "count": len(results),
        "courses": results
    })

@csrf_exempt
def update_course(request, course_id):

    if request.method != "PUT":
        return JsonResponse({
            "error": "Only PUT requests are allowed"
        }, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON"
        }, status=400)

    # Validate course ID
    try:
        object_id = ObjectId(course_id)
    except InvalidId:
        return JsonResponse({
            "error": "Invalid course ID"
        }, status=400)

    # Check whether course exists
    existing_course = courses_collection.find_one({
        "_id": object_id
    })

    if existing_course is None:
        return JsonResponse({
            "error": "Course not found"
        }, status=404)

    allowed_fields = [
        "course_name",
        "course_code",
        "degree",
        "duration_years",
        "total_seats",
        "tuition_fee",
        "eligibility",
        "admission_exam"
    ]

    update_data = {}

    for field in allowed_fields:
        if field in data:
            update_data[field] = data[field]

    if not update_data:
        return JsonResponse({
            "error": "No valid fields provided for update"
        }, status=400)

    # Prevent duplicate course code
    if "course_code" in update_data:

        duplicate_course = courses_collection.find_one({
            "college_id": existing_course["college_id"],
            "course_code": update_data["course_code"],
            "_id": {"$ne": object_id}
        })

        if duplicate_course:
            return JsonResponse({
                "error": "Course code already exists for this college"
            }, status=409)

    courses_collection.update_one(
        {"_id": object_id},
        {"$set": update_data}
    )

    updated_course = courses_collection.find_one({
        "_id": object_id
    })

    updated_course["_id"] = str(updated_course["_id"])

    return JsonResponse({
        "message": "Course updated successfully",
        "course": updated_course
    })


@csrf_exempt
def deactivate_course(request, course_id):

    if request.method != "PATCH":
        return JsonResponse({
            "error": "Only PATCH requests are allowed"
        }, status=405)

    try:
        object_id = ObjectId(course_id)
    except InvalidId:
        return JsonResponse({
            "error": "Invalid course ID"
        }, status=400)

    course = courses_collection.find_one({
        "_id": object_id
    })

    if course is None:
        return JsonResponse({
            "error": "Course not found"
        }, status=404)

    courses_collection.update_one(
        {"_id": object_id},
        {
            "$set": {
                "is_active": False
            }
        }
    )

    return JsonResponse({
        "message": "Course deactivated successfully"
    })