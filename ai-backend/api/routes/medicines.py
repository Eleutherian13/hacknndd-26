from fastapi import APIRouter, Depends
from core.database import get_database

router = APIRouter()

@router.get("/")
async def list_medicines(db=Depends(get_database)):
    """List all available medicines"""
    medicines = await db.medicines.find().limit(50).to_list(length=50)
    return {"medicines": medicines}

@router.get("/{medicine_id}")
async def get_medicine(medicine_id: str, db=Depends(get_database)):
    """Get medicine details"""
    medicine = await db.medicines.find_one({"_id": medicine_id})
    return {"medicine": medicine}
