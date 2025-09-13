# Linux Mirror Testing Solution - API Router

from fastapi import APIRouter
from .endpoints.test import router as test_router

router = APIRouter()

# Include the test router with proper prefix and tags
router.include_router(test_router, prefix="/test", tags=["test"])
