"""
FRONTEND API CLIENT
===================
Reusable API client library for connecting to Role 3 backend.

Usage:
    from frontend_api_client import APIClient
    
    client = APIClient(base_url="http://localhost:8000")
    prediction = client.predict("user_001", {"subscription_type": "Free"})
"""

import requests
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# API CLIENT
# ============================================================================

class APIClient:
    """
    REST API client for Spotify Churn Prediction backend.
    
    Attributes:
        base_url: Backend API base URL
        timeout: Request timeout in seconds
        headers: HTTP headers
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        """
        Initialize API client.
        
        Args:
            base_url: Backend API URL (default: http://localhost:8000)
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.headers = {"Content-Type": "application/json"}
    
    # ========================================================================
    # HEALTH & METADATA
    # ========================================================================
    
    def health(self) -> bool:
        """
        Check backend API health.
        
        Returns:
            True if backend is healthy, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5,
                headers=self.headers
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    def get_health_status(self) -> Optional[Dict[str, Any]]:
        """
        Get detailed health status.
        
        Returns:
            Health status dict with service details
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=10,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return None
    
    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Get backend metrics.
        
        Returns:
            Metrics dict with performance stats
        """
        try:
            response = requests.get(
                f"{self.base_url}/metrics",
                timeout=10,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return None
    
    # ========================================================================
    # PREDICTION ENDPOINTS
    # ========================================================================
    
    def predict(
        self,
        user_id: str,
        features: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Make single churn prediction.
        
        Args:
            user_id: Unique user identifier
            features: Feature dictionary (e.g., subscription_type, num_sessions)
        
        Returns:
            Prediction result with churn_probability and risk_segment
        """
        try:
            payload = {
                "user_id": user_id,
                "features": features
            }
            
            response = requests.post(
                f"{self.base_url}/predict",
                json=payload,
                timeout=self.timeout,
                headers=self.headers
            )
            response.raise_for_status()
            
            logger.info(f"Prediction for {user_id}: {response.json()['churn_probability']:.2%}")
            return response.json()
        
        except requests.exceptions.Timeout:
            logger.error("Prediction request timed out")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to backend at {self.base_url}")
            return None
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return None
    
    def predict_batch(
        self,
        predictions: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Make batch predictions.
        
        Args:
            predictions: List of prediction requests
                [{"user_id": "user_001", "features": {...}}, ...]
        
        Returns:
            Batch result with results list
        """
        try:
            payload = {
                "batch_id": f"batch_{int(datetime.now().timestamp())}",
                "predictions": predictions
            }
            
            response = requests.post(
                f"{self.base_url}/predict/batch",
                json=payload,
                timeout=self.timeout * 2,  # Longer timeout for batch
                headers=self.headers
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Batch prediction completed: {result['success_count']} succeeded")
            return result
        
        except Exception as e:
            logger.error(f"Batch prediction error: {e}")
            return None
    
    # ========================================================================
    # EXPLANATION ENDPOINTS
    # ========================================================================
    
    def explain(
        self,
        user_id: str,
        prediction_id: str,
        depth: str = "detailed",
        include_similar_users: bool = True,
        include_interactions: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Generate explanation for prediction.
        
        Args:
            user_id: User ID
            prediction_id: Prediction ID from predict()
            depth: Explanation depth - "basic", "detailed", or "expert"
            include_similar_users: Include similar user analysis
            include_interactions: Include feature interactions
        
        Returns:
            Explanation dict with SHAP values and text rationale
        """
        try:
            payload = {
                "user_id": user_id,
                "prediction_id": prediction_id,
                "explanation_depth": depth,
                "include_similar_users": include_similar_users,
                "include_interactions": include_interactions
            }
            
            response = requests.post(
                f"{self.base_url}/explain",
                json=payload,
                timeout=self.timeout * 2,
                headers=self.headers
            )
            response.raise_for_status()
            
            logger.info(f"Explanation generated for {user_id}")
            return response.json()
        
        except Exception as e:
            logger.error(f"Explanation error: {e}")
            return None
    
    # ========================================================================
    # PLAYBOOK ENDPOINTS
    # ========================================================================
    
    def recommend_playbooks(
        self,
        user_id: str,
        prediction_id: str,
        churn_probability: float,
        risk_segment: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get playbook recommendations.
        
        Args:
            user_id: User ID
            prediction_id: Prediction ID
            churn_probability: Churn probability (0-1)
            risk_segment: Risk segment (low_risk, medium_risk, high_risk)
        
        Returns:
            Playbook recommendations with best playbook
        """
        try:
            payload = {
                "user_id": user_id,
                "prediction_id": prediction_id,
                "churn_probability": churn_probability,
                "risk_segment": risk_segment
            }
            
            response = requests.post(
                f"{self.base_url}/playbook/recommend",
                json=payload,
                timeout=self.timeout,
                headers=self.headers
            )
            response.raise_for_status()
            
            logger.info(f"Playbooks recommended for {user_id}")
            return response.json()
        
        except Exception as e:
            logger.error(f"Playbook recommendation error: {e}")
            return None
    
    def execute_playbook(
        self,
        user_id: str,
        prediction_id: str,
        playbook_id: str,
        authorize: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a playbook.
        
        Args:
            user_id: User ID
            prediction_id: Prediction ID
            playbook_id: ID of playbook to execute
            authorize: Must be True to execute
        
        Returns:
            Execution result with execution_id and status
        """
        try:
            if not authorize:
                logger.warning("Playbook execution requires authorization")
                return None
            
            payload = {
                "user_id": user_id,
                "prediction_id": prediction_id,
                "playbook_id": playbook_id,
                "authorize_execution": True
            }
            
            response = requests.post(
                f"{self.base_url}/playbook/execute",
                json=payload,
                timeout=self.timeout,
                headers=self.headers
            )
            response.raise_for_status()
            
            logger.info(f"Playbook {playbook_id} executed for {user_id}")
            return response.json()
        
        except Exception as e:
            logger.error(f"Playbook execution error: {e}")
            return None
    
    # ========================================================================
    # CHATBOT ENDPOINTS
    # ========================================================================
    
    def chat(
        self,
        user_id: str,
        session_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send message to chatbot.
        
        Args:
            user_id: User ID
            session_id: Chat session ID
            message: User message
            context: Optional context (e.g., churn_probability)
        
        Returns:
            Chat response with assistant message and suggested actions
        """
        try:
            payload = {
                "user_id": user_id,
                "session_id": session_id,
                "messages": [{"role": "user", "content": message}],
                "context": context or {}
            }
            
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                timeout=self.timeout,
                headers=self.headers
            )
            response.raise_for_status()
            
            logger.info(f"Chat message received from {user_id}")
            return response.json()
        
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return None
    
    # ========================================================================
    # ERROR HANDLING & UTILITIES
    # ========================================================================
    
    def test_connection(self) -> bool:
        """Test connection to backend"""
        return self.health()
    
    def get_error_message(self, response: requests.Response) -> str:
        """Extract error message from response"""
        try:
            error_data = response.json()
            return error_data.get("detail", str(response.text))
        except:
            return response.text


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example usage
    client = APIClient()
    
    # Check health
    if client.health():
        print("✅ Backend is healthy")
        
        # Make prediction
        prediction = client.predict("user_001", {
            "subscription_type": "Free",
            "num_sessions": 10,
            "monthly_stream_hours": 5.5
        })
        
        if prediction:
            print(f"Churn Probability: {prediction['churn_probability']:.2%}")
            print(f"Risk Segment: {prediction['risk_segment']}")
            
            # Get explanation
            explanation = client.explain(
                "user_001",
                prediction['prediction_id']
            )
            
            if explanation:
                print(f"Summary: {explanation['summary']}")
            
            # Get playbooks
            playbooks = client.recommend_playbooks(
                "user_001",
                prediction['prediction_id'],
                prediction['churn_probability'],
                prediction['risk_segment']
            )
            
            if playbooks:
                print(f"Best Playbook: {playbooks['best_playbook_id']}")
    else:
        print("❌ Backend is offline")
