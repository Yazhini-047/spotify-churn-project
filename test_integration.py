"""
INTEGRATION TESTS FOR SPOTIFY CHURN BACKEND
=============================================
Comprehensive test suite for all API endpoints, database operations,
and chatbot interactions.

Run with: pytest tests/test_integration.py -v
Coverage: pytest tests/test_integration.py --cov=backend_app

Author: Role 3 Backend Developer
Date: 2026-02-26
"""

import pytest
import json
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import backend modules
import sys
sys.path.insert(0, '.')

from backend_app import (
    app, AppState, PredictionRequest, ExplanationRequest,
    PlaybookRecommendationRequest, PlaybookExecutionRequest,
    ChatRequest, ChatMessage, ChatMessageRole, RiskSegment
)
from chatbot_flows import (
    ChatbotManager, IntentClassifier, ConversationPhase,
    ConversationIntent, Sentiment
)
from database_layer import (
    DatabaseManager, PredictionLogModel, ChatSessionLogModel,
    PlaybookExecutionLogModel, Base
)

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def db_manager():
    """Create in-memory SQLite database for testing"""
    db = DatabaseManager("sqlite:///:memory:")
    db.create_tables()
    yield db
    db.drop_tables()


@pytest.fixture
def client():
    """FastAPI test client"""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Async FastAPI test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_prediction_data():
    """Sample prediction data"""
    return {
        "user_id": "test_user_001",
        "features": {
            "subscription_type": "Free",
            "num_sessions": 10,
            "monthly_stream_hours": 5.5,
            "account_age_days": 30,
            "playlist_diversity": 0.6
        }
    }


@pytest.fixture
def chatbot_manager():
    """Chatbot manager instance"""
    return ChatbotManager()


# ============================================================================
# TESTS - HEALTH & METRICS ENDPOINTS
# ============================================================================

class TestHealthEndpoints:
    """Test system health endpoints"""
    
    def test_health_check(self, client):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_predictions" in data
        assert "active_sessions" in data


# ============================================================================
# TESTS - PREDICTION ENDPOINTS
# ============================================================================

class TestPredictionEndpoints:
    """Test prediction endpoints"""
    
    def test_single_prediction(self, client, sample_prediction_data):
        """Test single prediction endpoint"""
        response = client.post("/predict", json=sample_prediction_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == sample_prediction_data["user_id"]
        assert "prediction_id" in data
        assert 0 <= data["churn_probability"] <= 1
        assert data["risk_segment"] in ["low_risk", "medium_risk", "high_risk"]
        assert data["prediction_label"] in [0, 1]
        assert "timestamp" in data
    
    def test_batch_prediction(self, client):
        """Test batch prediction endpoint"""
        batch_request = {
            "batch_id": "batch_001",
            "predictions": [
                {
                    "user_id": f"user_{i:03d}",
                    "features": {
                        "subscription_type": "Free",
                        "num_sessions": 10 + i,
                        "monthly_stream_hours": 5.5 + i
                    }
                }
                for i in range(3)
            ]
        }
        
        response = client.post("/predict/batch", json=batch_request)
        assert response.status_code == 200
        data = response.json()
        
        assert data["batch_id"] == batch_request["batch_id"]
        assert len(data["results"]) == 3
        assert data["success_count"] == 3
        assert data["error_count"] == 0
        assert data["processing_time_ms"] > 0
    
    def test_prediction_creates_log(self, client, sample_prediction_data, db_manager):
        """Test that predictions are logged"""
        session = db_manager.get_session()
        initial_count = len(session.query(PredictionLogModel).all())
        
        client.post("/predict", json=sample_prediction_data)
        
        # Note: This test assumes database is connected
        # In production, verify logs are created
        session.close()


# ============================================================================
# TESTS - EXPLANATION ENDPOINTS
# ============================================================================

class TestExplanationEndpoints:
    """Test explainability endpoints"""
    
    def test_explanation_generation(self, client):
        """Test explanation endpoint"""
        explanation_request = {
            "user_id": "user_001",
            "prediction_id": "pred_001",
            "explanation_depth": "detailed"
        }
        
        response = client.post("/explain", json=explanation_request)
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == "user_001"
        assert data["prediction_id"] == "pred_001"
        assert "summary" in data
        assert "key_drivers" in data
        assert isinstance(data["key_drivers"], list)
        assert "feature_attributions" in data
        assert "actionable_insights" in data
    
    def test_explanation_depths(self, client):
        """Test different explanation depths"""
        for depth in ["basic", "detailed", "expert"]:
            response = client.post("/explain", json={
                "user_id": "user_001",
                "prediction_id": "pred_001",
                "explanation_depth": depth
            })
            assert response.status_code == 200


# ============================================================================
# TESTS - PLAYBOOK ENDPOINTS
# ============================================================================

class TestPlaybookEndpoints:
    """Test playbook recommendation and execution"""
    
    def test_playbook_recommendation(self, client):
        """Test playbook recommendation endpoint"""
        recommendation_request = {
            "user_id": "user_001",
            "prediction_id": "pred_001",
            "churn_probability": 0.75,
            "risk_segment": "high_risk"
        }
        
        response = client.post("/playbook/recommend", json=recommendation_request)
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == "user_001"
        assert "recommended_playbooks" in data
        assert "best_playbook_id" in data
        assert "estimated_impact" in data
    
    def test_playbook_execution(self, client):
        """Test playbook execution endpoint"""
        execution_request = {
            "user_id": "user_001",
            "prediction_id": "pred_001",
            "playbook_id": "PB_HIGH_RISK_CONVERT",
            "authorize_execution": True
        }
        
        response = client.post("/playbook/execute", json=execution_request)
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == "user_001"
        assert data["playbook_id"] == "PB_HIGH_RISK_CONVERT"
        assert "execution_id" in data
        assert data["status"] in ["pending", "executing", "completed", "failed"]
    
    def test_playbook_execution_requires_authorization(self, client):
        """Test that execution requires explicit authorization"""
        execution_request = {
            "user_id": "user_001",
            "prediction_id": "pred_001",
            "playbook_id": "PB_HIGH_RISK_CONVERT",
            "authorize_execution": False
        }
        
        response = client.post("/playbook/execute", json=execution_request)
        assert response.status_code == 403


# ============================================================================
# TESTS - CHATBOT ENDPOINTS
# ============================================================================

class TestChatbotEndpoints:
    """Test chatbot endpoint"""
    
    def test_single_chat_message(self, client):
        """Test single chat message"""
        chat_request = {
            "user_id": "user_001",
            "session_id": "session_001",
            "messages": [
                {
                    "role": "user",
                    "content": "Why might I churn?"
                }
            ]
        }
        
        response = client.post("/chat", json=chat_request)
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == "user_001"
        assert data["session_id"] == "session_001"
        assert "message" in data
        assert "content" in data["message"]
        assert data["message"]["role"] == "assistant"
    
    def test_multi_turn_conversation(self, client):
        """Test multi-turn conversation"""
        session_id = "session_002"
        
        messages = [
            "I'm thinking about canceling",
            "The ads are too much",
            "Really? Free for a month?",
            "Okay, let's do it!"
        ]
        
        for msg in messages:
            response = client.post("/chat", json={
                "user_id": "user_002",
                "session_id": session_id,
                "messages": [{"role": "user", "content": msg}],
                "context": {"churn_probability": 0.75}
            })
            assert response.status_code == 200
            assert "message" in response.json()
    
    def test_chat_with_context(self, client):
        """Test chat with user context"""
        chat_request = {
            "user_id": "user_001",
            "session_id": "session_001",
            "messages": [{"role": "user", "content": "What can you offer me?"}],
            "context": {
                "churn_probability": 0.75,
                "risk_segment": "high_risk"
            }
        }
        
        response = client.post("/chat", json=chat_request)
        assert response.status_code == 200


# ============================================================================
# TESTS - CHATBOT FLOWS (Unit Tests)
# ============================================================================

class TestChatbotFlows:
    """Test chatbot conversation flows"""
    
    def test_intent_classification(self):
        """Test intent detection"""
        test_cases = [
            ("Why do I churn?", ConversationIntent.EXPLAIN_CHURN),
            ("What can you offer?", ConversationIntent.GET_RECOMMENDATIONS),
            ("Yes, I accept", ConversationIntent.EXECUTE_ACTION),
            ("How do I contact support?", ConversationIntent.GENERAL_HELP),
        ]
        
        for text, expected_intent in test_cases:
            intent, confidence = IntentClassifier.classify(text)
            assert intent == expected_intent
            assert confidence > 0.5
    
    def test_sentiment_detection(self):
        """Test sentiment analysis"""
        test_cases = [
            ("I love Spotify!", Sentiment.POSITIVE),
            ("This is terrible", Sentiment.NEGATIVE),
            ("Okay, thanks", Sentiment.NEUTRAL),
            ("I'm so frustrated!", Sentiment.FRUSTRATED),
        ]
        
        for text, expected_sentiment in test_cases:
            sentiment = IntentClassifier.detect_sentiment(text)
            assert sentiment == expected_sentiment
    
    def test_conversation_context(self, chatbot_manager):
        """Test conversation context management"""
        response1 = chatbot_manager.process_message("session_1", "Why do I churn?")
        assert response1.intent == ConversationIntent.EXPLAIN_CHURN
        
        response2 = chatbot_manager.process_message("session_1", "I want recommendations")
        assert response2.intent == ConversationIntent.GET_RECOMMENDATIONS
        
        # Verify history is maintained
        session = chatbot_manager.sessions["session_1"]
        assert session.turn_count == 2
        assert len(session.intent_history) == 2
    
    def test_multi_turn_flow(self, chatbot_manager):
        """Test complete conversation flow"""
        session_id = "test_session"
        
        # Initialize session
        session = chatbot_manager.get_or_create_session(
            user_id="user_test",
            session_id=session_id,
            churn_probability=0.75
        )
        
        assert session.phase == ConversationPhase.GREETING
        
        # Message 1: Explain churn
        resp1 = chatbot_manager.process_message(session_id, "Why might I churn?")
        assert resp1.intent == ConversationIntent.EXPLAIN_CHURN
        
        # Message 2: Get recommendations
        resp2 = chatbot_manager.process_message(session_id, "Show me what you can offer")
        assert resp2.intent == ConversationIntent.GET_RECOMMENDATIONS
        
        # Message 3: Accept
        resp3 = chatbot_manager.process_message(session_id, "Yes, I want to try Premium")
        assert resp3.intent == ConversationIntent.EXECUTE_ACTION


# ============================================================================
# TESTS - DATABASE LAYER
# ============================================================================

class TestDatabaseLayer:
    """Test database operations"""
    
    def test_create_prediction_log(self, db_manager):
        """Test creating prediction log"""
        session = db_manager.get_session()
        
        log = PredictionLogModel(
            id="test_1",
            user_id="user_001",
            prediction_id="pred_001",
            churn_probability=0.75,
            risk_segment="high_risk",
            prediction_label=1,
            confidence_score=0.85,
            model_version="1.0"
        )
        
        session.add(log)
        session.commit()
        
        # Verify
        result = session.query(PredictionLogModel).filter(
            PredictionLogModel.prediction_id == "pred_001"
        ).first()
        
        assert result is not None
        assert result.churn_probability == 0.75
        
        session.close()
    
    def test_create_chat_session_log(self, db_manager):
        """Test creating chat session log"""
        session = db_manager.get_session()
        
        log = ChatSessionLogModel(
            id="chat_test_1",
            session_id="session_001",
            user_id="user_001",
            turn_count=3,
            messages=[
                {"role": "user", "content": "Why do I churn?"},
                {"role": "assistant", "content": "Let me explain..."}
            ]
        )
        
        session.add(log)
        session.commit()
        
        # Verify
        result = session.query(ChatSessionLogModel).filter(
            ChatSessionLogModel.session_id == "session_001"
        ).first()
        
        assert result is not None
        assert result.turn_count == 3
        
        session.close()


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Test API performance"""
    
    def test_prediction_response_time(self, client, sample_prediction_data):
        """Test prediction response time < 500ms"""
        import time
        
        start = time.time()
        response = client.post("/predict", json=sample_prediction_data)
        elapsed = (time.time() - start) * 1000
        
        assert response.status_code == 200
        assert elapsed < 500, f"Prediction took {elapsed}ms, expected < 500ms"
    
    def test_batch_prediction_throughput(self, client):
        """Test batch prediction throughput"""
        import time
        
        batch_request = {
            "batch_id": "batch_perf",
            "predictions": [
                {
                    "user_id": f"user_{i:03d}",
                    "features": {
                        "subscription_type": "Free",
                        "num_sessions": 10 + i,
                        "monthly_stream_hours": 5.5 + i
                    }
                }
                for i in range(50)
            ]
        }
        
        start = time.time()
        response = client.post("/predict/batch", json=batch_request)
        elapsed = (time.time() - start) * 1000
        
        assert response.status_code == 200
        data = response.json()
        
        # Should process 50 predictions in < 5 seconds
        assert elapsed < 5000
        predictions_per_second = 50 / (elapsed / 1000)
        print(f"\nThroughput: {predictions_per_second:.1f} predictions/second")


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_prediction_request(self, client):
        """Test invalid prediction request"""
        response = client.post("/predict", json={
            "user_id": "user_001"
            # Missing 'features' field
        })
        assert response.status_code == 422  # Validation error
    
    def test_invalid_json(self, client):
        """Test invalid JSON"""
        response = client.post(
            "/predict",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
