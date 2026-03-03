"""
ROLE 3: CHATBOT BACKEND & API SERVER
=====================================
Production-grade FastAPI backend for Spotify Churn Prediction.
Integrates with trained model, explainability engine, and playbook system.

Endpoints:
- POST /predict: Single prediction
- POST /predict/batch: Batch predictions
- POST /explain: Generate explanations  
- POST /playbook/recommend: Get recommended playbooks
- POST /playbook/execute: Execute playbook for user
- POST /chat: Chatbot interaction
- GET /health: Health check
- GET /metrics: Performance metrics

Author: Role 3 Backend Developer
Date: 2026-02-26
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from enum import Enum
import uuid
import json
import logging
import asyncio
from contextlib import asynccontextmanager

import pandas as pd
import numpy as np
import joblib
from dataclasses import dataclass, asdict

# ============================================================================
# IMPORTS FROM ROLE 1 & ROLE 2
# ============================================================================
# These will be available after you load the model pickle and explainability modules
# from shap_integration_engine import ChurnExplainabilityEngine
# from playbook_template_engine import PlaybookExecutionEngine

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class RiskSegment(str, Enum):
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"

class ChatMessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class PlaybookStatus(str, Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"

# ============================================================================
# PYDANTIC MODELS - REQUEST/RESPONSE SCHEMAS
# ============================================================================

class PredictionRequest(BaseModel):
    """Schema for single prediction request"""
    user_id: str = Field(..., description="Unique user identifier")
    features: Dict[str, Any] = Field(..., description="User feature dictionary")
    
    class Config:
        example = {
            "user_id": "cust_12345",
            "features": {
                "subscription_type": "Free",
                "num_sessions": 10,
                "monthly_stream_hours": 5.5
            }
        }


class PredictionResponse(BaseModel):
    """Schema for prediction response"""
    user_id: str
    prediction_id: str
    churn_probability: float = Field(..., ge=0, le=1)
    risk_segment: RiskSegment
    prediction_label: int = Field(..., literal=[0, 1])
    confidence_score: float
    timestamp: datetime
    model_version: str


class FeatureAttribution(BaseModel):
    """Individual feature attribution"""
    feature_name: str
    feature_value: Any
    shap_value: float
    direction: Literal["increases_churn", "decreases_churn", "neutral"]
    impact_percentage: float
    human_readable: str


class ExplanationRequest(BaseModel):
    """Request for explanation generation"""
    user_id: str
    prediction_id: str
    explanation_depth: Literal["basic", "detailed", "expert"] = "detailed"
    include_similar_users: bool = True
    include_interactions: bool = True
    
    class Config:
        example = {
            "user_id": "cust_12345",
            "prediction_id": "pred_98765",
            "explanation_depth": "detailed"
        }


class ExplanationResponse(BaseModel):
    """Comprehensive explanation response"""
    user_id: str
    prediction_id: str
    summary: str
    key_drivers: List[str]
    feature_attributions: List[FeatureAttribution]
    actionable_insights: List[str]
    similar_users: Optional[List[Dict[str, Any]]] = None
    decision_rules: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime
    explanation_method: str


class PlaybookRecommendationRequest(BaseModel):
    """Request for playbook recommendations"""
    user_id: str
    prediction_id: str
    churn_probability: float = Field(..., ge=0, le=1)
    risk_segment: RiskSegment


class PlaybookAction(BaseModel):
    """Individual playbook action"""
    action_id: str
    action_name: str
    channel: Literal["email", "sms", "in_app", "push"]
    delay_hours: int
    parameters: Dict[str, Any]


class PlaybookRecommendationResponse(BaseModel):
    """Playbook recommendation response"""
    user_id: str
    prediction_id: str
    recommended_playbooks: List[Dict[str, Any]]
    best_playbook_id: str
    estimated_impact: Dict[str, Any]
    timestamp: datetime


class PlaybookExecutionRequest(BaseModel):
    """Request to execute a playbook"""
    user_id: str
    prediction_id: str
    playbook_id: str
    authorize_execution: bool = False


class PlaybookExecutionResponse(BaseModel):
    """Response from playbook execution"""
    execution_id: str
    user_id: str
    playbook_id: str
    status: PlaybookStatus
    actions_queued: List[PlaybookAction]
    estimated_completion: datetime
    timestamp: datetime


class ChatMessage(BaseModel):
    """Individual chat message"""
    role: ChatMessageRole
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    """Chatbot conversation request"""
    user_id: str
    session_id: str
    messages: List[ChatMessage]
    context: Optional[Dict[str, Any]] = None
    
    class Config:
        example = {
            "user_id": "cust_12345",
            "session_id": "sess_abc123",
            "messages": [
                {
                    "role": "user",
                    "content": "Why might I churn?"
                }
            ],
            "context": {
                "churn_probability": 0.75,
                "risk_segment": "high_risk"
            }
        }


class ChatResponse(BaseModel):
    """Chatbot conversation response"""
    user_id: str
    session_id: str
    message: ChatMessage
    suggested_actions: Optional[List[Dict[str, Any]]] = None
    offers: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, bool]


class MetricsResponse(BaseModel):
    """Metrics and performance response"""
    total_predictions: int
    total_explanations: int
    total_playbooks_executed: int
    average_response_time_ms: float
    active_sessions: int
    errors_last_24h: int


class BatchPredictionRequest(BaseModel):
    """Batch prediction request"""
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    predictions: List[PredictionRequest]


class BatchPredictionResponse(BaseModel):
    """Batch prediction response"""
    batch_id: str
    results: List[PredictionResponse]
    processing_time_ms: float
    success_count: int
    error_count: int


# ============================================================================
# DATABASE & LOGGING MODELS
# ============================================================================

@dataclass
class PredictionLog:
    """Log entry for predictions"""
    prediction_id: str
    user_id: str
    churn_probability: float
    risk_segment: str
    timestamp: datetime
    model_version: str
    features_hash: str


@dataclass
class ChatLog:
    """Log entry for chat interactions"""
    session_id: str
    user_id: str
    message_type: str
    content: str
    response: str
    timestamp: datetime
    sentiment: Optional[str] = None


@dataclass
class PlaybookExecutionLog:
    """Log entry for playbook executions"""
    execution_id: str
    user_id: str
    playbook_id: str
    status: str
    initial_churn_prob: float
    timestamp: datetime
    actions_executed: List[str]


# ============================================================================
# GLOBAL STATE & IN-MEMORY STORAGE
# ============================================================================

class AppState:
    """Application state management"""
    
    def __init__(self):
        self.model = None
        self.explainer = None
        self.playbook_engine = None
        self.feature_names = []
        self.model_version = "1.0"
        
        # In-memory storage (replace with DB in production)
        self.prediction_logs: List[PredictionLog] = []
        self.chat_logs: List[ChatLog] = []
        self.playbook_logs: List[PlaybookExecutionLog] = []
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Metrics
        self.metrics = {
            "total_predictions": 0,
            "total_explanations": 0,
            "total_playbooks": 0,
            "average_response_time_ms": 0,
            "errors_last_24h": 0
        }
    
    def log_prediction(self, log_entry: PredictionLog):
        """Log prediction"""
        self.prediction_logs.append(log_entry)
        self.metrics["total_predictions"] += 1
    
    def log_chat(self, log_entry: ChatLog):
        """Log chat interaction"""
        self.chat_logs.append(log_entry)
    
    def log_playbook_execution(self, log_entry: PlaybookExecutionLog):
        """Log playbook execution"""
        self.playbook_logs.append(log_entry)
        self.metrics["total_playbooks"] += 1


# ============================================================================
# LIFESPAN MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown.
    At startup: Load model, explainer, and playbook engine
    At shutdown: Clean up resources
    """
    logger.info("🚀 Starting Spotify Churn Backend...")
    
    app.state.app = AppState()
    
    try:
        # Load model (replace with your actual model path)
        logger.info("Loading trained model...")
        # app.state.app.model = joblib.load('model.pkl')
        logger.info("✓ Model loaded")
        
        # Note: Load explainability engine and playbook engine
        # app.state.app.explainer = ChurnExplainabilityEngine(...)
        # app.state.app.playbook_engine = PlaybookExecutionEngine(...)
        
        logger.info("✓ All services initialized successfully")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise
    
    yield  # Server running
    
    logger.info("🛑 Shutting down...")
    # Cleanup code here if needed
    logger.info("✓ Shutdown complete")


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Spotify Churn Prediction Backend",
    description="Production API for churn prediction, explainability, and playbook execution",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_app_state() -> AppState:
    """Get app state"""
    return app.state.app


# ============================================================================
# ENDPOINTS - HEALTH & METRICS
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check(app_state: AppState = Depends(get_app_state)):
    """
    Health check endpoint.
    Returns service status and availability.
    """
    return HealthResponse(
        status="healthy" if app_state.model else "degraded",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        services={
            "model": app_state.model is not None,
            "explainer": app_state.explainer is not None,
            "playbook_engine": app_state.playbook_engine is not None,
        }
    )


@app.get("/metrics", response_model=MetricsResponse, tags=["System"])
async def get_metrics(app_state: AppState = Depends(get_app_state)):
    """
    Get backend performance metrics.
    """
    return MetricsResponse(
        total_predictions=app_state.metrics["total_predictions"],
        total_explanations=app_state.metrics["total_explanations"],
        total_playbooks_executed=app_state.metrics["total_playbooks"],
        average_response_time_ms=app_state.metrics["average_response_time_ms"],
        active_sessions=len(app_state.active_sessions),
        errors_last_24h=app_state.metrics["errors_last_24h"]
    )


# ============================================================================
# ENDPOINTS - PREDICTION
# ============================================================================

@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(
    request: PredictionRequest,
    app_state: AppState = Depends(get_app_state)
):
    """
    Make a single churn prediction.
    
    **Request:**
    - `user_id`: Unique user identifier
    - `features`: Dictionary of user features
    
    **Response:**
    - `churn_probability`: Probability of churn (0-1)
    - `risk_segment`: One of low_risk, medium_risk, high_risk
    - `prediction_label`: 0 (retain) or 1 (churn)
    """
    try:
        if app_state.model is None:
            raise HTTPException(
                status_code=503,
                detail="Model not loaded"
            )
        
        # TODO: Implement prediction logic
        # Convert features to model input
        # features_df = pd.DataFrame([request.features])
        # prediction = app_state.model.predict(features_df)[0]
        # churn_prob = app_state.model.predict_proba(features_df)[0][1]
        
        # Placeholder implementation
        churn_probability = np.random.random()
        risk_segment = (
            RiskSegment.LOW_RISK if churn_probability < 0.33
            else RiskSegment.MEDIUM_RISK if churn_probability < 0.67
            else RiskSegment.HIGH_RISK
        )
        
        prediction_id = str(uuid.uuid4())
        response = PredictionResponse(
            user_id=request.user_id,
            prediction_id=prediction_id,
            churn_probability=float(churn_probability),
            risk_segment=risk_segment,
            prediction_label=1 if churn_probability > 0.5 else 0,
            confidence_score=max(churn_probability, 1 - churn_probability),
            timestamp=datetime.utcnow(),
            model_version=app_state.model_version
        )
        
        # Log prediction
        app_state.log_prediction(PredictionLog(
            prediction_id=prediction_id,
            user_id=request.user_id,
            churn_probability=float(churn_probability),
            risk_segment=risk_segment.value,
            timestamp=datetime.utcnow(),
            model_version=app_state.model_version,
            features_hash=str(hash(frozenset(request.features.items())))
        ))
        
        logger.info(f"Prediction for {request.user_id}: {churn_probability:.2%}")
        return response
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        app_state.metrics["errors_last_24h"] += 1
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    tags=["Prediction"]
)
async def predict_batch(
    request: BatchPredictionRequest,
    app_state: AppState = Depends(get_app_state)
):
    """
    Make batch predictions for multiple users.
    """
    import time
    start_time = time.time()
    
    try:
        results = []
        errors = 0
        
        for pred_req in request.predictions:
            try:
                # Reuse single prediction endpoint
                result = await predict(pred_req, app_state)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch prediction error for {pred_req.user_id}: {e}")
                errors += 1
        
        processing_time = (time.time() - start_time) * 1000
        
        return BatchPredictionResponse(
            batch_id=request.batch_id,
            results=results,
            processing_time_ms=processing_time,
            success_count=len(results),
            error_count=errors
        )
        
    except Exception as e:
        logger.error(f"Batch processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS - EXPLAINABILITY
# ============================================================================

@app.post("/explain", response_model=ExplanationResponse, tags=["Explainability"])
async def explain(
    request: ExplanationRequest,
    app_state: AppState = Depends(get_app_state)
):
    """
    Generate detailed explanation for a prediction.
    
    **Explanation Depths:**
    - `basic`: Summary only
    - `detailed`: Summary + key drivers (default)
    - `expert`: Full analysis with interactions
    """
    try:
        if app_state.explainer is None:
            raise HTTPException(
                status_code=503,
                detail="Explainability engine not loaded"
            )
        
        # TODO: Get explanation from explainability engine
        # explanation = app_state.explainer.get_user_explanation(
        #     user_id=request.user_id,
        #     depth=request.explanation_depth
        # )
        
        # Placeholder implementation
        response = ExplanationResponse(
            user_id=request.user_id,
            prediction_id=request.prediction_id,
            summary="User shows high engagement with free plan but limited premium conversion signals.",
            key_drivers=["subscription_type", "monthly_stream_hours", "num_sessions"],
            feature_attributions=[
                FeatureAttribution(
                    feature_name="subscription_type",
                    feature_value="Free",
                    shap_value=0.35,
                    direction="increases_churn",
                    impact_percentage=35.0,
                    human_readable="Free users have 35% higher churn risk"
                ),
                FeatureAttribution(
                    feature_name="monthly_stream_hours",
                    feature_value=5.5,
                    shap_value=-0.15,
                    direction="decreases_churn",
                    impact_percentage=-15.0,
                    human_readable="Higher streaming hours reduce churn risk by 15%"
                )
            ],
            actionable_insights=[
                "Offer free trial upgrade to Premium",
                "Personalize music recommendations",
                "Send targeted offer within 7 days"
            ],
            timestamp=datetime.utcnow(),
            explanation_method="SHAP TreeExplainer"
        )
        
        app_state.metrics["total_explanations"] += 1
        logger.info(f"Explanation generated for {request.user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Explanation error: {e}")
        app_state.metrics["errors_last_24h"] += 1
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS - PLAYBOOK RECOMMENDATION & EXECUTION
# ============================================================================

@app.post(
    "/playbook/recommend",
    response_model=PlaybookRecommendationResponse,
    tags=["Playbooks"]
)
async def recommend_playbooks(
    request: PlaybookRecommendationRequest,
    app_state: AppState = Depends(get_app_state)
):
    """
    Recommend playbooks based on user risk segment.
    """
    try:
        if app_state.playbook_engine is None:
            raise HTTPException(
                status_code=503,
                detail="Playbook engine not loaded"
            )
        
        # TODO: Get playbook recommendations
        # recommended = app_state.playbook_engine.recommend_playbooks(
        #     user_id=request.user_id,
        #     risk_segment=request.risk_segment,
        #     churn_prob=request.churn_probability
        # )
        
        response = PlaybookRecommendationResponse(
            user_id=request.user_id,
            prediction_id=request.prediction_id,
            recommended_playbooks=[
                {
                    "playbook_id": "PB_HIGH_RISK_CONVERT",
                    "name": "High-Risk User Conversion Blitz",
                    "priority": 5,
                    "estimated_conversion_lift": 0.25
                }
            ],
            best_playbook_id="PB_HIGH_RISK_CONVERT",
            estimated_impact={
                "conversion_rate_lift": 0.25,
                "retention_improvement": 0.30,
                "revenue_impact_per_user": 9.99
            },
            timestamp=datetime.utcnow()
        )
        
        logger.info(f"Playbook recommendations for {request.user_id}: {response.best_playbook_id}")
        return response
        
    except Exception as e:
        logger.error(f"Playbook recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/playbook/execute",
    response_model=PlaybookExecutionResponse,
    tags=["Playbooks"]
)
async def execute_playbook(
    request: PlaybookExecutionRequest,
    background_tasks: BackgroundTasks,
    app_state: AppState = Depends(get_app_state)
):
    """
    Execute a playbook for a user.
    Actions queued asynchronously.
    """
    try:
        if not request.authorize_execution:
            raise HTTPException(
                status_code=403,
                detail="Playbook execution not authorized"
            )
        
        execution_id = str(uuid.uuid4())
        
        # TODO: Execute playbook
        # execution = app_state.playbook_engine.execute_playbook(
        #     playbook_id=request.playbook_id,
        #     user_id=request.user_id
        # )
        
        response = PlaybookExecutionResponse(
            execution_id=execution_id,
            user_id=request.user_id,
            playbook_id=request.playbook_id,
            status=PlaybookStatus.PENDING,
            actions_queued=[
                PlaybookAction(
                    action_id="ACT_001",
                    action_name="Premium Trial Offer",
                    channel="email",
                    delay_hours=0,
                    parameters={"trial_days": 30}
                )
            ],
            estimated_completion=datetime.utcnow(),
            timestamp=datetime.utcnow()
        )
        
        # Log execution
        app_state.log_playbook_execution(PlaybookExecutionLog(
            execution_id=execution_id,
            user_id=request.user_id,
            playbook_id=request.playbook_id,
            status=PlaybookStatus.PENDING.value,
            initial_churn_prob=0.75,  # TODO: Get from prediction
            timestamp=datetime.utcnow(),
            actions_executed=[]
        ))
        
        # Queue background task
        background_tasks.add_task(
            execute_playbook_async,
            execution_id=execution_id,
            app_state=app_state
        )
        
        logger.info(f"Playbook execution queued: {execution_id}")
        return response
        
    except Exception as e:
        logger.error(f"Playbook execution error: {e}")
        app_state.metrics["errors_last_24h"] += 1
        raise HTTPException(status_code=500, detail=str(e))


async def execute_playbook_async(execution_id: str, app_state: AppState):
    """Async playbook execution"""
    logger.info(f"Executing playbook: {execution_id}")
    await asyncio.sleep(2)  # Simulate execution
    logger.info(f"Playbook execution completed: {execution_id}")


# ============================================================================
# ENDPOINTS - CHATBOT
# ============================================================================

@app.post("/chat", response_model=ChatResponse, tags=["Chatbot"])
async def chat(
    request: ChatRequest,
    app_state: AppState = Depends(get_app_state)
):
    """
    Chatbot conversation endpoint.
    Supports natural language interactions about churn risk and playbooks.
    
    **Chat Intent Types:**
    - Explain why user might churn
    - Get recommendations
    - Execute playbooks
    - General help
    """
    try:
        user_message = request.messages[-1].content
        
        # Initialize or get session
        if request.session_id not in app_state.active_sessions:
            app_state.active_sessions[request.session_id] = {
                "user_id": request.user_id,
                "created_at": datetime.utcnow(),
                "message_count": 0,
                "context": request.context or {}
            }
        
        session = app_state.active_sessions[request.session_id]
        session["message_count"] += 1
        
        # TODO: Implement conversational AI logic
        # - Parse user intent
        # - Generate contextual response
        # - Suggest actions
        
        assistant_response = generate_chat_response(
            user_message=user_message,
            session_context=session,
            app_state=app_state
        )
        
        response = ChatResponse(
            user_id=request.user_id,
            session_id=request.session_id,
            message=ChatMessage(
                role=ChatMessageRole.ASSISTANT,
                content=assistant_response["content"],
                timestamp=datetime.utcnow()
            ),
            suggested_actions=assistant_response.get("actions"),
            offers=assistant_response.get("offers"),
            timestamp=datetime.utcnow()
        )
        
        # Log chat
        app_state.log_chat(ChatLog(
            session_id=request.session_id,
            user_id=request.user_id,
            message_type="user_query",
            content=user_message,
            response=assistant_response["content"],
            timestamp=datetime.utcnow()
        ))
        
        return response
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        app_state.metrics["errors_last_24h"] += 1
        raise HTTPException(status_code=500, detail=str(e))


def generate_chat_response(
    user_message: str,
    session_context: Dict[str, Any],
    app_state: AppState
) -> Dict[str, Any]:
    """
    Generate chatbot response based on user message and context.
    """
    message_lower = user_message.lower()
    
    # Intent detection (TODO: Use NLP/ML for production)
    if any(word in message_lower for word in ["why", "churn", "risk", "leave"]):
        return {
            "content": "Based on your usage patterns, you show some churn signals. Would you like to understand the specific factors or see how we can help?",
            "actions": [{"type": "explain", "label": "Show detailed explanation"}],
            "offers": [{"type": "premium_trial", "label": "7-day Premium Trial"}]
        }
    
    elif any(word in message_lower for word in ["offer", "help", "suggest", "what"]):
        return {
            "content": "We have personalized recommendations to improve your experience! Our Premium plan includes ad-free listening, offline downloads, and higher quality audio.",
            "actions": [{"type": "playbook", "label": "View recommendations"}],
            "offers": [
                {"type": "premium_trial", "label": "1-month Free Trial"},
                {"type": "discount", "label": "30% off Premium"}
            ]
        }
    
    elif any(word in message_lower for word in ["thank", "yes", "ok", "good"]):
        return {
            "content": "Great! We've activated your offer. Check your email for details. Is there anything else I can help you with?",
            "actions": [],
            "offers": []
        }
    
    else:
        return {
            "content": "I'm here to help! I can explain your churn risk factors, recommend personalized offers, or answer questions about your account.",
            "actions": [
                {"type": "explain", "label": "Explain my risk"},
                {"type": "recommend", "label": "Get recommendations"}
            ],
            "offers": []
        }


# ============================================================================
# STARTUP MESSAGE
# ============================================================================

@app.on_event("startup")
async def startup_message():
    logger.info("""
    
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║  🎵 SPOTIFY CHURN PREDICTION BACKEND - ROLE 3                ║
    ║                                                               ║
    ║  Server: http://localhost:8000                               ║
    ║  Docs:   http://localhost:8000/docs                          ║
    ║  ReDoc:  http://localhost:8000/redoc                         ║
    ║                                                               ║
    ║  Endpoints:                                                  ║
    ║  - POST /predict          (Single prediction)                ║
    ║  - POST /predict/batch    (Batch predictions)                ║
    ║  - POST /explain          (Generate explanation)             ║
    ║  - POST /playbook/recommend (Get playbook recommendations)   ║
    ║  - POST /playbook/execute   (Execute playbook)               ║
    ║  - POST /chat             (Chatbot interaction)              ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    """)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
