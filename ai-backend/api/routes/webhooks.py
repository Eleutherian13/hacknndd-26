from fastapi import APIRouter, Request
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/n8n")
async def n8n_webhook(request: Request):
    """Handle n8n webhook callbacks"""
    data = await request.json()
    logger.info(f"Received n8n webhook: {data}")
    return {"status": "received"}

@router.post("/zapier")
async def zapier_webhook(request: Request):
    """Handle Zapier webhook callbacks"""
    data = await request.json()
    logger.info(f"Received Zapier webhook: {data}")
    return {"status": "received"}

@router.post("/cms")
async def cms_webhook(request: Request):
    """Handle CMS sync webhook"""
    data = await request.json()
    logger.info(f"Received CMS webhook: {data}")
    return {"status": "received"}
