"""
API SPECIFICATION - OpenAPI/Swagger
===================================
Complete REST API specification for the Spotify Churn Prediction Backend.

This specification can be viewed at:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)
- /openapi.json (Raw JSON spec)

Endpoints:
- GET  /health           - Health check
- GET  /metrics          - Performance metrics
- POST /predict          - Single prediction
- POST /predict/batch    - Batch predictions
- POST /explain          - Generate explanation
- POST /playbook/recommend - Get playbook recommendations
- POST /playbook/execute   - Execute playbook
- POST /chat             - Chatbot interaction
"""

import json
from typing import Dict, Any

# OpenAPI 3.1.0 specification
OPENAPI_SPEC: Dict[str, Any] = {
    "openapi": "3.1.0",
    "info": {
        "title": "Spotify Churn Prediction Backend",
        "version": "1.0.0",
        "description": """
        Production-grade REST API for Spotify churn prediction, explainability, 
        and playbook-driven interventions.
        
        ## Overview
        This API provides:
        - **Predictions**: Real-time churn probability forecasting
        - **Explanations**: SHAP-based feature attributions
        - **Playbooks**: Automated intervention recommendations
        - **Chatbot**: Natural language interface
        
        ## Authentication
        Optional: Add bearer token authentication
        
        ## Rate Limiting
        - Standard: 100 requests/minute
        - Batch: 10 requests/minute
        - Chat: 30 requests/minute
        
        ## Error Handling
        All errors return standardized JSON format:
        ```json
        {
            "detail": "Error message",
            "status_code": 400,
            "timestamp": "2026-02-26T12:34:56Z"
        }
        ```
        """,
        "contact": {
            "name": "Backend Team",
            "email": "backend@spotify-churn.com"
        },
        "license": {
            "name": "Proprietary"
        }
    },
    "servers": [
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.spotify-churn.com",
            "description": "Production server"
        }
    ],
    "paths": {
        "/health": {
            "get": {
                "summary": "Health Check",
                "description": "Check API and service health status",
                "tags": ["System"],
                "responses": {
                    "200": {
                        "description": "Service is healthy",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HealthResponse"
                                },
                                "example": {
                                    "status": "healthy",
                                    "timestamp": "2026-02-26T12:34:56Z",
                                    "version": "1.0.0",
                                    "services": {
                                        "model": True,
                                        "explainer": True,
                                        "playbook_engine": True
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/metrics": {
            "get": {
                "summary": "Performance Metrics",
                "description": "Get backend performance and usage metrics",
                "tags": ["System"],
                "responses": {
                    "200": {
                        "description": "Metrics retrieved successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/MetricsResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/predict": {
            "post": {
                "summary": "Make Prediction",
                "description": "Generate a single churn prediction for a user",
                "tags": ["Prediction"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/PredictionRequest"
                            },
                            "example": {
                                "user_id": "cust_12345",
                                "features": {
                                    "subscription_type": "Free",
                                    "num_sessions": 10,
                                    "monthly_stream_hours": 5.5,
                                    "account_age_days": 30
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Prediction generated successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/PredictionResponse"
                                }
                            }
                        }
                    },
                    "422": {
                        "description": "Validation error in request"
                    },
                    "500": {
                        "description": "Internal server error"
                    }
                }
            }
        },
        "/predict/batch": {
            "post": {
                "summary": "Batch Predictions",
                "description": "Make predictions for multiple users efficiently",
                "tags": ["Prediction"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/BatchPredictionRequest"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Batch predictions completed",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/BatchPredictionResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/explain": {
            "post": {
                "summary": "Generate Explanation",
                "description": """
                Generate detailed explanation for a prediction including:
                - SHAP feature attributions
                - Text rationale
                - Similar users
                - Decision rules
                """,
                "tags": ["Explainability"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ExplanationRequest"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Explanation generated",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ExplanationResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/playbook/recommend": {
            "post": {
                "summary": "Recommend Playbooks",
                "description": """
                Get recommended intervention playbooks based on:
                - Churn risk level
                - User segment
                - Historical success rates
                """,
                "tags": ["Playbooks"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/PlaybookRecommendationRequest"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Playbook recommendations",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/PlaybookRecommendationResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/playbook/execute": {
            "post": {
                "summary": "Execute Playbook",
                "description": """
                Execute a playbook for a user. This queues actions:
                - Requires explicit authorization
                - Actions executed asynchronously
                - Returns execution ID for tracking
                """,
                "tags": ["Playbooks"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/PlaybookExecutionRequest"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Playbook execution queued",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/PlaybookExecutionResponse"
                                }
                            }
                        }
                    },
                    "403": {
                        "description": "Execution not authorized"
                    }
                }
            }
        },
        "/chat": {
            "post": {
                "summary": "Chatbot",
                "description": """
                Conversational interface for:
                - Explaining churn risk
                - Getting recommendations
                - Executing offers
                - General support
                
                Supports multi-turn conversations with intent detection.
                """,
                "tags": ["Chatbot"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ChatRequest"
                            },
                            "example": {
                                "user_id": "cust_12345",
                                "session_id": "sess_abc123",
                                "messages": [
                                    {
                                        "role": "user",
                                        "content": "Why might I churn?"
                                    }
                                ],
                                "context": {
                                    "churn_probability": 0.75
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Chatbot response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ChatResponse"
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "HealthResponse": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["healthy", "degraded"]},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "version": {"type": "string"},
                    "services": {
                        "type": "object",
                        "properties": {
                            "model": {"type": "boolean"},
                            "explainer": {"type": "boolean"},
                            "playbook_engine": {"type": "boolean"}
                        }
                    }
                }
            },
            "MetricsResponse": {
                "type": "object",
                "properties": {
                    "total_predictions": {"type": "integer"},
                    "total_explanations": {"type": "integer"},
                    "total_playbooks_executed": {"type": "integer"},
                    "average_response_time_ms": {"type": "number"},
                    "active_sessions": {"type": "integer"},
                    "errors_last_24h": {"type": "integer"}
                }
            },
            "PredictionRequest": {
                "type": "object",
                "required": ["user_id", "features"],
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "Unique user identifier"
                    },
                    "features": {
                        "type": "object",
                        "description": "User feature dictionary",
                        "additionalProperties": {}
                    }
                }
            },
            "PredictionResponse": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "prediction_id": {"type": "string", "format": "uuid"},
                    "churn_probability": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1
                    },
                    "risk_segment": {
                        "type": "string",
                        "enum": ["low_risk", "medium_risk", "high_risk"]
                    },
                    "prediction_label": {"type": "integer", "enum": [0, 1]},
                    "confidence_score": {"type": "number"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "model_version": {"type": "string"}
                }
            },
            "BatchPredictionRequest": {
                "type": "object",
                "properties": {
                    "batch_id": {"type": "string"},
                    "predictions": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/PredictionRequest"}
                    }
                }
            },
            "BatchPredictionResponse": {
                "type": "object",
                "properties": {
                    "batch_id": {"type": "string"},
                    "results": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/PredictionResponse"}
                    },
                    "processing_time_ms": {"type": "number"},
                    "success_count": {"type": "integer"},
                    "error_count": {"type": "integer"}
                }
            },
            "ExplanationRequest": {
                "type": "object",
                "required": ["user_id", "prediction_id"],
                "properties": {
                    "user_id": {"type": "string"},
                    "prediction_id": {"type": "string"},
                    "explanation_depth": {
                        "type": "string",
                        "enum": ["basic", "detailed", "expert"],
                        "default": "detailed"
                    }
                }
            },
            "ExplanationResponse": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "prediction_id": {"type": "string"},
                    "summary": {"type": "string"},
                    "key_drivers": {"type": "array", "items": {"type": "string"}},
                    "feature_attributions": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/FeatureAttribution"}
                    },
                    "actionable_insights": {"type": "array", "items": {"type": "string"}}
                }
            },
            "FeatureAttribution": {
                "type": "object",
                "properties": {
                    "feature_name": {"type": "string"},
                    "feature_value": {},
                    "shap_value": {"type": "number"},
                    "direction": {
                        "type": "string",
                        "enum": ["increases_churn", "decreases_churn", "neutral"]
                    },
                    "impact_percentage": {"type": "number"},
                    "human_readable": {"type": "string"}
                }
            },
            "PlaybookRecommendationRequest": {
                "type": "object",
                "required": ["user_id", "prediction_id", "churn_probability", "risk_segment"],
                "properties": {
                    "user_id": {"type": "string"},
                    "prediction_id": {"type": "string"},
                    "churn_probability": {"type": "number", "minimum": 0, "maximum": 1},
                    "risk_segment": {
                        "type": "string",
                        "enum": ["low_risk", "medium_risk", "high_risk"]
                    }
                }
            },
            "PlaybookRecommendationResponse": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "recommended_playbooks": {"type": "array"},
                    "best_playbook_id": {"type": "string"},
                    "estimated_impact": {"type": "object"}
                }
            },
            "PlaybookExecutionRequest": {
                "type": "object",
                "required": ["user_id", "playbook_id"],
                "properties": {
                    "user_id": {"type": "string"},
                    "playbook_id": {"type": "string"},
                    "authorize_execution": {
                        "type": "boolean",
                        "default": False
                    }
                }
            },
            "PlaybookExecutionResponse": {
                "type": "object",
                "properties": {
                    "execution_id": {"type": "string", "format": "uuid"},
                    "playbook_id": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "executing", "completed", "failed"]
                    },
                    "actions_queued": {"type": "array"},
                    "estimated_completion": {"type": "string", "format": "date-time"}
                }
            },
            "ChatRequest": {
                "type": "object",
                "required": ["user_id", "session_id", "messages"],
                "properties": {
                    "user_id": {"type": "string"},
                    "session_id": {"type": "string"},
                    "messages": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/ChatMessage"}
                    },
                    "context": {"type": "object", "additionalProperties": {}}
                }
            },
            "ChatMessage": {
                "type": "object",
                "properties": {
                    "role": {"type": "string", "enum": ["user", "assistant"]},
                    "content": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"}
                }
            },
            "ChatResponse": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "session_id": {"type": "string"},
                    "message": {"$ref": "#/components/schemas/ChatMessage"},
                    "suggested_actions": {"type": "array"},
                    "offers": {"type": "array"}
                }
            }
        }
    }
}


def save_spec(filename: str = "openapi.json"):
    """Save OpenAPI spec to file"""
    with open(filename, "w") as f:
        json.dump(OPENAPI_SPEC, f, indent=2)
    print(f"✓ OpenAPI specification saved to {filename}")


def get_spec_dict() -> Dict[str, Any]:
    """Get OpenAPI spec as dictionary"""
    return OPENAPI_SPEC


if __name__ == "__main__":
    save_spec()
    print("\nOpenAPI Specification Generated")
    print("\nView at:")
    print("  - Swagger UI: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print("  - Raw JSON: GET http://localhost:8000/openapi.json")
