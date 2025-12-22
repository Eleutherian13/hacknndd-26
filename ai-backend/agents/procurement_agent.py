from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Dict, List, Optional
import logging
import httpx

from core.config import settings

logger = logging.getLogger(__name__)


class ProcurementAgent:
    """AI Agent for automating procurement and supplier orders"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.AGENT_MODEL,
            temperature=0.5,
            api_key=settings.OPENAI_API_KEY
        )
    
    async def check_inventory_need(
        self,
        medicine_id: str,
        current_stock: int,
        reorder_threshold: int,
        pending_orders: int = 0
    ) -> Dict:
        """
        Check if procurement is needed for a medicine
        
        Args:
            medicine_id: Medicine ID
            current_stock: Current stock level
            reorder_threshold: Minimum stock before reordering
            pending_orders: Number of units in pending customer orders
        
        Returns:
            Dict with procurement recommendation
        """
        try:
            effective_stock = current_stock - pending_orders
            needs_procurement = effective_stock <= reorder_threshold
            
            if needs_procurement:
                # Calculate suggested order quantity
                # Order enough to reach 3x the reorder threshold
                suggested_quantity = max(
                    (reorder_threshold * 3) - effective_stock,
                    reorder_threshold
                )
                
                urgency = "high" if effective_stock < 0 else "medium" if effective_stock < reorder_threshold / 2 else "low"
                
                logger.info(f"Procurement needed for {medicine_id}: {suggested_quantity} units")
                
                return {
                    "needs_procurement": True,
                    "medicine_id": medicine_id,
                    "current_stock": current_stock,
                    "pending_orders": pending_orders,
                    "effective_stock": effective_stock,
                    "suggested_quantity": suggested_quantity,
                    "urgency": urgency,
                    "reason": f"Stock level ({effective_stock}) below threshold ({reorder_threshold})"
                }
            else:
                return {
                    "needs_procurement": False,
                    "medicine_id": medicine_id,
                    "current_stock": current_stock,
                    "effective_stock": effective_stock
                }
                
        except Exception as e:
            logger.error(f"Error checking inventory need: {str(e)}")
            return {"needs_procurement": False, "error": str(e)}
    
    async def generate_purchase_order(
        self,
        procurement_items: List[Dict],
        supplier_info: Dict
    ) -> Dict:
        """
        Generate a purchase order for supplier
        
        Args:
            procurement_items: List of items to order
            supplier_info: Supplier contact and details
        
        Returns:
            Purchase order data
        """
        try:
            # Generate PO using LLM for natural language formatting
            items_text = "\n".join([
                f"- {item['medicine_name']}: {item['quantity']} units (SKU: {item['sku']})"
                for item in procurement_items
            ])
            
            prompt = f"""Generate a professional purchase order email for a pharmacy supplier:

Supplier: {supplier_info.get('name', 'Supplier')}
Items needed:
{items_text}

Include:
1. Professional greeting
2. Clear itemized list
3. Expected delivery timeframe
4. Payment terms reference
5. Contact information for questions

Keep it concise and business-appropriate.
"""
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a procurement assistant generating purchase orders."),
                HumanMessage(content=prompt)
            ])
            
            po_number = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            purchase_order = {
                "po_number": po_number,
                "supplier": supplier_info,
                "items": procurement_items,
                "total_items": len(procurement_items),
                "total_quantity": sum(item['quantity'] for item in procurement_items),
                "generated_email": response.content,
                "created_at": datetime.now().isoformat(),
                "status": "draft"
            }
            
            logger.info(f"Generated purchase order: {po_number}")
            return purchase_order
            
        except Exception as e:
            logger.error(f"Error generating purchase order: {str(e)}")
            return {"error": str(e)}
    
    async def send_to_supplier(
        self,
        purchase_order: Dict,
        method: str = "n8n"
    ) -> bool:
        """
        Send purchase order to supplier via configured integration
        
        Args:
            purchase_order: PO data
            method: Integration method (n8n, zapier, email)
        
        Returns:
            Success status
        """
        try:
            if method == "n8n" and settings.N8N_WEBHOOK_URL:
                return await self._send_via_n8n(purchase_order)
            elif method == "zapier" and settings.ZAPIER_WEBHOOK_URL:
                return await self._send_via_zapier(purchase_order)
            else:
                logger.warning(f"No valid integration configured for method: {method}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending to supplier: {str(e)}")
            return False
    
    async def _send_via_n8n(self, purchase_order: Dict) -> bool:
        """Send PO via n8n webhook"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.N8N_WEBHOOK_URL + "procurement",
                    json=purchase_order,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully sent PO {purchase_order['po_number']} via n8n")
                    return True
                else:
                    logger.error(f"n8n webhook failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending via n8n: {str(e)}")
            return False
    
    async def _send_via_zapier(self, purchase_order: Dict) -> bool:
        """Send PO via Zapier webhook"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.ZAPIER_WEBHOOK_URL + "procurement",
                    json=purchase_order,
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Successfully sent PO {purchase_order['po_number']} via Zapier")
                    return True
                else:
                    logger.error(f"Zapier webhook failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending via Zapier: {str(e)}")
            return False
    
    async def auto_procure_if_enabled(
        self,
        inventory_check_results: List[Dict]
    ) -> List[Dict]:
        """
        Automatically create and send purchase orders if auto-procurement is enabled
        
        Args:
            inventory_check_results: Results from inventory checks
        
        Returns:
            List of generated purchase orders
        """
        if not settings.ENABLE_AUTO_PROCUREMENT:
            logger.info("Auto-procurement is disabled")
            return []
        
        # Filter items that need procurement
        items_to_order = [
            item for item in inventory_check_results 
            if item.get('needs_procurement') and item.get('urgency') in ['high', 'medium']
        ]
        
        if not items_to_order:
            return []
        
        # Group by supplier (simplified - assumes single supplier)
        supplier_info = {
            "name": "Default Supplier",
            "email": "supplier@example.com"
        }
        
        # Generate PO
        po = await self.generate_purchase_order(items_to_order, supplier_info)
        
        # Send to supplier
        if po and not po.get('error'):
            success = await self.send_to_supplier(po, method="n8n")
            po['sent'] = success
            return [po]
        
        return []


from datetime import datetime
