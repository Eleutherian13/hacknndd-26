from fastapi import APIRouter

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard():
    """Get admin dashboard data"""
    return {"message": "Admin dashboard data"}

@router.get("/inventory")
async def get_inventory():
    """Get inventory status"""
    return {"message": "Inventory data"}

@router.get("/agents/logs")
async def get_agent_logs():
    """Get agent activity logs"""
    return {"message": "Agent logs"}
