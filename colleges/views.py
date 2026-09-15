from django.shortcuts import render
from django.http import JsonResponse
from bson import ObjectId
from bson.errors import InvalidId

from .mongodb import colleges_collection
from django.views.decorators.csrf import csrf_exempt

import json


#searching colleges that are similar
def search_colleges(request):

    search_query = request.GET.get("search", "").strip()

    if not search_query:
        return JsonResponse({
            "message": "Please enter a college name"
        })

    colleges = colleges_collection.find({
        "$or": [
            {
                "college_name": {
                    "$regex": search_query,
                    "$options": "i"
                }
            },
            {
                "college_short_name": {
                    "$regex": search_query,
                    "$options": "i"
                }
            }
        ]
    })

    results = []

    for college in colleges:
        results.append({
            "id": str(college["_id"]),
            "college_name": college.get("college_name"),
            "state": college.get("state"),
            "city": college.get("city"),
            "college_type": college.get("college_type"),
            "institute_code": college.get("institute_code")
        })

    return JsonResponse({
        "count": len(results),
        "results": results
    })

#returns the details of a college based on the college id
def college_details(request, college_id):

    try:
        college = colleges_collection.find_one({
            "_id": ObjectId(college_id)
        })
    except InvalidId:
        return JsonResponse({
            "error": "Invalid college ID"
        }, status=400)

    if college is None:
        return JsonResponse({
            "error": "College not found"
        }, status=404)

    college["_id"] = str(college["_id"])

    return JsonResponse(college)



#adding college to the database
@csrf_exempt
def add_college(request):

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
        "college_name",
        "college_short_name",
        "state",
        "city",
        "nirf_ranking",
        "acres",
        "established_year",
        "total_intake",
        "tuition_fee",
        "hostel_fee",
        "highest_package",
        "average_package",
        "placement_percentage",
        "college_logo",
        "institute_code",
        "college_type"
    ]

    for field in required_fields:
        if field not in data:
            return JsonResponse({
                "error": f"{field} is required"
            }, status=400)

    existing_college = colleges_collection.find_one({
        "institute_code": data["institute_code"]
    })

    if existing_college:
        return JsonResponse({
            "error": "Institute code already exists"
        }, status=409)

    data["is_active"] = True

    result = colleges_collection.insert_one(data)

    return JsonResponse({
        "message": "College added successfully",
        "college_id": str(result.inserted_id)
    }, status=201)


#updating the college details based on the college id
@csrf_exempt
def update_college(request, college_id):

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

    # Check whether the college ID is valid
    try:
        object_id = ObjectId(college_id)
    except InvalidId:
        return JsonResponse({
            "error": "Invalid college ID"
        }, status=400)

    # Check whether the college exists
    existing_college = colleges_collection.find_one({
        "_id": object_id
    })

    if existing_college is None:
        return JsonResponse({
            "error": "College not found"
        }, status=404)

    # Fields that are allowed to be updated
    allowed_fields = [
        "college_name",
        "college_short_name",
        "state",
        "city",
        "nirf_ranking",
        "acres",
        "established_year",
        "total_intake",
        "tuition_fee",
        "hostel_fee",
        "highest_package",
        "average_package",
        "placement_percentage",
        "college_logo",
        "institute_code",
        "college_type"
    ]

    update_data = {}

    for field in allowed_fields:
        if field in data:
            update_data[field] = data[field]

    if not update_data:
        return JsonResponse({
            "error": "No valid fields provided for update"
        }, status=400)

    # Check duplicate institute code
    if "institute_code" in update_data:

        duplicate = colleges_collection.find_one({
            "institute_code": update_data["institute_code"],
            "_id": {"$ne": object_id}
        })

        if duplicate:
            return JsonResponse({
                "error": "Institute code already exists"
            }, status=409)

    # Update MongoDB document
    colleges_collection.update_one(
        {"_id": object_id},
        {"$set": update_data}
    )

    # Get updated college
    updated_college = colleges_collection.find_one({
        "_id": object_id
    })

    updated_college["_id"] = str(updated_college["_id"])

    return JsonResponse({
        "message": "College updated successfully",
        "college": updated_college
    })

#deleting or deactivating a college based on the college id
@csrf_exempt
def deactivate_college(request, college_id):

    if request.method != "PATCH":
        return JsonResponse({
            "error": "Only PATCH requests are allowed"
        }, status=405)

    try:
        object_id = ObjectId(college_id)
    except InvalidId:
        return JsonResponse({
            "error": "Invalid college ID"
        }, status=400)

    college = colleges_collection.find_one({
        "_id": object_id
    })

    if college is None:
        return JsonResponse({
            "error": "College not found"
        }, status=404)

    colleges_collection.update_one(
        {"_id": object_id},
        {
            "$set": {
                "is_active": False
            }
        }
    )

    return JsonResponse({
        "message": "College deactivated successfully"
    })