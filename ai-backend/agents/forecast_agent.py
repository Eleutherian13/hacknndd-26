from langchain_openai import ChatOpenAI
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
import logging

from core.config import settings
from models.prediction import PredictionConfidence

logger = logging.getLogger(__name__)

# Lazy import LinearRegression only when needed
try:
    from sklearn.linear_model import LinearRegression
except ImportError:
    logger.warning("scikit-learn not fully available, using numpy only")
    LinearRegression = None


class ForecastAgent:
    """AI Agent for predicting medicine depletion and refill needs"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.AGENT_MODEL,
            temperature=0.3,  # Lower temperature for more consistent predictions
            api_key=settings.OPENAI_API_KEY
        )
    
    async def predict_depletion(
        self,
        user_id: str,
        medicine_id: str,
        order_history: List[Dict]
    ) -> Optional[Dict]:
        """
        Predict when a medicine will run out based on order history
        
        Args:
            user_id: User ID
            medicine_id: Medicine ID
            order_history: List of previous orders with dates and quantities
        
        Returns:
            Prediction data or None if insufficient data
        """
        try:
            # Need minimum orders for prediction
            if len(order_history) < settings.PREDICTION_MIN_ORDERS:
                logger.info(f"Insufficient data for prediction: {len(order_history)} orders")
                return None
            
            # Prepare data for analysis
            df = pd.DataFrame(order_history)
            df['order_date'] = pd.to_datetime(df['order_date'])
            df = df.sort_values('order_date')
            
            # Calculate consumption rate
            consumption_rate = self._calculate_consumption_rate(df)
            
            if consumption_rate <= 0:
                logger.warning("Invalid consumption rate calculated")
                return None
            
            # Get last order details
            last_order = df.iloc[-1]
            last_order_date = last_order['order_date'].date()
            last_quantity = last_order['quantity']
            
            # Predict depletion date
            days_to_deplete = last_quantity / consumption_rate
            predicted_depletion_date = last_order_date + timedelta(days=days_to_deplete)
            
            # Suggest reorder date (7 days before depletion)
            suggested_reorder_date = predicted_depletion_date - timedelta(days=7)
            
            # Calculate confidence based on order consistency
            confidence_score = self._calculate_confidence(df)
            confidence_level = self._get_confidence_level(confidence_score)
            
            # Suggest reorder quantity (average of last 3 orders)
            recent_orders = df.tail(3)['quantity'].tolist()
            suggested_quantity = int(np.mean(recent_orders))
            
            logger.info(f"Prediction for {medicine_id}: depletion on {predicted_depletion_date}")
            
            return {
                "user_id": user_id,
                "medicine_id": medicine_id,
                "medicine_name": last_order.get('medicine_name', ''),
                "average_consumption_rate": round(consumption_rate, 2),
                "last_order_date": last_order_date,
                "last_order_quantity": int(last_quantity),
                "predicted_depletion_date": predicted_depletion_date,
                "suggested_reorder_date": max(suggested_reorder_date, date.today()),
                "suggested_quantity": suggested_quantity,
                "confidence": confidence_level,
                "confidence_score": round(confidence_score, 2),
                "historical_data": order_history
            }
            
        except Exception as e:
            logger.error(f"Error in forecast agent: {str(e)}", exc_info=True)
            return None
    
    def _calculate_consumption_rate(self, df: pd.DataFrame) -> float:
        """Calculate average daily consumption rate"""
        if len(df) < 2:
            return 0.0
        
        # Calculate days between orders and quantities
        df['days_since_last'] = df['order_date'].diff().dt.days
        df['daily_consumption'] = df['quantity'].shift(1) / df['days_since_last']
        
        # Remove first row (no previous order) and invalid values
        valid_rates = df['daily_consumption'].dropna()
        valid_rates = valid_rates[valid_rates > 0]
        
        if len(valid_rates) == 0:
            return 0.0
        
        # Return average consumption rate
        return valid_rates.mean()
    
    def _calculate_confidence(self, df: pd.DataFrame) -> float:
        """Calculate prediction confidence based on order consistency"""
        if len(df) < 2:
            return 0.5
        
        # Calculate standard deviation of order intervals
        df['days_since_last'] = df['order_date'].diff().dt.days
        intervals = df['days_since_last'].dropna()
        
        if len(intervals) == 0:
            return 0.5
        
        # Lower std deviation = higher confidence
        mean_interval = intervals.mean()
        std_interval = intervals.std()
        
        # Calculate coefficient of variation
        if mean_interval > 0:
            cv = std_interval / mean_interval
            # Convert to confidence score (0-1)
            confidence = max(0.0, min(1.0, 1.0 - cv))
        else:
            confidence = 0.5
        
        return confidence
    
    def _get_confidence_level(self, score: float) -> PredictionConfidence:
        """Convert confidence score to level"""
        if score >= settings.PREDICTION_CONFIDENCE_THRESHOLD:
            return PredictionConfidence.HIGH
        elif score >= 0.5:
            return PredictionConfidence.MEDIUM
        else:
            return PredictionConfidence.LOW
    
    async def generate_predictions_for_user(
        self,
        user_id: str,
        all_order_history: Dict[str, List[Dict]]
    ) -> List[Dict]:
        """
        Generate predictions for all medicines a user regularly orders
        
        Args:
            user_id: User ID
            all_order_history: Dict mapping medicine_id to order history
        
        Returns:
            List of prediction dicts
        """
        predictions = []
        
        for medicine_id, order_history in all_order_history.items():
            prediction = await self.predict_depletion(user_id, medicine_id, order_history)
            if prediction:
                predictions.append(prediction)
        
        logger.info(f"Generated {len(predictions)} predictions for user {user_id}")
        return predictions
    
    async def should_notify_user(self, prediction: Dict) -> bool:
        """Determine if user should be notified about upcoming depletion"""
        try:
            predicted_date = prediction['predicted_depletion_date']
            if isinstance(predicted_date, str):
                predicted_date = datetime.fromisoformat(predicted_date).date()
            
            days_until_depletion = (predicted_date - date.today()).days
            
            # Notify if:
            # 1. Within 7 days of depletion
            # 2. High confidence prediction
            # 3. Not already notified recently
            should_notify = (
                days_until_depletion <= 7 and
                days_until_depletion >= 0 and
                prediction.get('confidence') == PredictionConfidence.HIGH
            )
            
            return should_notify
            
        except Exception as e:
            logger.error(f"Error checking notification criteria: {str(e)}")
            return False
