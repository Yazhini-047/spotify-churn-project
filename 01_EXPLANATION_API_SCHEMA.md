# Explanation API Specification for Spotify Churn Prediction

## 1. Overview
This document specifies the API schema for generating explainable AI outputs, including SHAP-based feature attributions and human-readable textual rationales.

**Version:** 1.0  
**Last Updated:** 2026-02-26  
**Owner:** Explainability Scientist

---

## 2. Core Data Models

### 2.1 UserExplanation Object
Represents a complete explanation for a single user's churn prediction.

```json
{
  "user_id": "string (UUID)",
  "prediction": {
    "churn_probability": "float (0-1)",
    "risk_segment": "string (low_risk|medium_risk|high_risk)",
    "prediction_label": "integer (0 = retain, 1 = churn)"
  },
  "base_case_explanation": {
    "base_value": "float",
    "model_output": "float",
    "explanation": "string"
  },
  "feature_attributions": [
    {
      "feature_name": "string",
      "feature_value": "float|string",
      "shap_value": "float",
      "attribution_strength": "string (critical|high|medium|low)",
      "direction": "string (increases_churn|decreases_churn)",
      "impact_percentage": "float (0-100)",
      "human_readable": "string"
    }
  ],
  "text_rationale": {
    "summary": "string (brief explanation)",
    "detailed": "string (full explanation)",
    "key_drivers": ["string"],
    "actionable_insights": ["string"]
  },
  "local_interpretability": {
    "similar_users": [
      {
        "user_id": "string",
        "similarity_score": "float (0-1)",
        "their_churn_probability": "float"
      }
    ],
    "feature_interactions": [
      {
        "feature_1": "string",
        "feature_2": "string",
        "interaction_effect": "float",
        "interpretation": "string"
      }
    ]
  },
  "decision_rules": [
    {
      "rule_id": "string",
      "rule_text": "string",
      "rule_triggers": "boolean",
      "confidence": "float (0-1)"
    }
  ],
  "metadata": {
    "timestamp": "ISO8601",
    "model_version": "string",
    "explanation_method": "string (SHAP|LIME|TreeExplainer)",
    "explanation_stability_score": "float (0-1)"
  }
}
```

---

### 2.2 ExplanationBatch Request
For requesting explanations for multiple users.

```json
{
  "request_id": "string (UUID)",
  "user_ids": ["string"],
  "include_fields": [
    "prediction",
    "feature_attributions",
    "text_rationale",
    "local_interpretability",
    "decision_rules"
  ],
  "explanation_depth": "string (basic|detailed|expert)",
  "model_version": "string (default: latest)",
  "options": {
    "include_similar_users": "boolean",
    "include_feature_interactions": "boolean",
    "n_features": "integer (default: 10)",
    "language": "string (english|spanish|french)"
  }
}
```

---

### 2.3 FeatureAttribution Object
Detailed breakdown of how each feature contributes to the prediction.

```json
{
  "feature_name": "string",
  "feature_type": "string (numerical|categorical|binary)",
  "original_value": "float|string",
  "normalized_value": "float",
  "shap_value": "float",
  "shap_base_value": "float",
  "shap_expected_value": "float",
  "attribution_percentage": "float (0-100)",
  "percentile": "float (0-100)",
  "direction": "string (increases_churn|decreases_churn)",
  "strength": "string (critical|high|medium|low|negligible)",
  "business_meaning": {
    "interpretation": "string",
    "example": "string",
    "actionability": "string"
  },
  "statistical_info": {
    "mean_across_population": "float",
    "std_across_population": "float",
    "comparison_to_avg": "float"
  }
}
```

---

### 2.4 PlaybookAction Object
Links explanations to specific business actions.

```json
{
  "playbook_id": "string",
  "action_id": "string",
  "triggered_by": ["string (feature_names)"],
  "condition": "string (logical expression)",
  "action_name": "string",
  "action_description": "string",
  "action_type": "string (offer|engagement|communication|retention)",
  "priority": "integer (1-5, 5 = highest)",
  "implementation": {
    "channel": "string (email|push|sms|in_app)",
    "template": "string (template_id)",
    "parameters": {
      "key": "value"
    }
  },
  "expected_impact": {
    "retention_probability_lift": "float (0-1)",
    "revenue_impact": "float (USD)",
    "success_metric": "string"
  }
}
```

---

## 3. API Endpoints Specification

### 3.1 GET /v1/explanations/{user_id}

**Description:** Get explanation for a single user  
**Authentication:** Required (Bearer token)  
**Rate Limit:** 1000 req/hour

**Request:**
```
GET /v1/explanations/user_12345?
  depth=detailed&
  include_similar=true&
  include_interactions=true
```

**Response (200):**
```json
{
  "status": "success",
  "data": { /* UserExplanation object */ },
  "metadata": {
    "request_id": "req_abc123",
    "processing_time_ms": 245
  }
}
```

**Error Response (400/404/500):**
```json
{
  "status": "error",
  "error_code": "USER_NOT_FOUND",
  "message": "User ID user_12345 not found in model training data",
  "request_id": "req_abc123"
}
```

---

### 3.2 POST /v1/explanations/batch

**Description:** Get explanations for multiple users  
**Rate Limit:** 100 req/hour

**Request:**
```json
{
  "user_ids": ["user_1", "user_2", "user_3"],
  "explanation_depth": "detailed",
  "options": {
    "include_similar_users": true,
    "n_features": 10
  }
}
```

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "explanations": [
      { /* UserExplanation objects */ }
    ],
    "summary_stats": {
      "total_processed": 3,
      "total_failed": 0,
      "average_churn_probability": 0.62
    }
  }
}
```

---

### 3.3 POST /v1/explanations/validate

**Description:** Validate explanation quality and stability  
**Rate Limit:** 500 req/hour

**Request:**
```json
{
  "explanation_id": "exp_xyz789",
  "validation_type": "stability|coherence|actionability"
}
```

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "explanation_id": "exp_xyz789",
    "stability_score": 0.87,
    "coherence_score": 0.91,
    "actionability_score": 0.78,
    "validation_passed": true,
    "issues": [],
    "recommendations": []
  }
}
```

---

### 3.4 POST /v1/playbooks/recommend

**Description:** Get recommended playbook actions for a user  
**Rate Limit:** 1000 req/hour

**Request:**
```json
{
  "user_id": "user_12345",
  "context": {
    "current_segment": "high_risk",
    "recent_behavior_change": "increased_skip_rate"
  }
}
```

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "user_id": "user_12345",
    "recommended_playbooks": [
      { /* PlaybookAction objects */ }
    ],
    "best_action": {
      "action_id": "action_premium_trial",
      "confidence": 0.92
    }
  }
}
```

---

### 3.5 GET /v1/explanations/stability-report

**Description:** Get stability report for all explanations  
**Rate Limit:** 100 req/hour

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "total_explanations": 5000,
    "average_stability_score": 0.84,
    "stability_distribution": {
      "stable (>0.8)": 4200,
      "moderate (0.6-0.8)": 700,
      "unstable (<0.6)": 100
    },
    "unstable_explanations": [
      {
        "user_id": "user_999",
        "stability_score": 0.45,
        "reason": "Feature values at distribution boundary"
      }
    ]
  }
}
```

---

## 4. Feature Attribution Schema

### 4.1 Attribution Levels

```
CRITICAL:     |SHAP| > 0.3 | Feature heavily influences prediction
HIGH:         |SHAP| > 0.15 | Feature significantly influences prediction
MEDIUM:       |SHAP| > 0.05 | Feature moderately influences prediction
LOW:          |SHAP| > 0.01 | Feature slightly influences prediction
NEGLIGIBLE:   |SHAP| ≤ 0.01 | Feature has minimal influence
```

### 4.2 Business Impact Mapping

```python
{
  "subscription_type_Free": {
    "shap_contribution": +0.25,
    "business_meaning": "Free users are 3x more likely to churn",
    "lever": "Convert to premium via incentives",
    "lever_strength": "HIGH"
  },
  "ads_listened_per_week": {
    "shap_contribution": +0.18,
    "business_meaning": "Each additional ad/week increases churn by ~2%",
    "lever": "Reduce ad load to <30/week",
    "lever_strength": "CRITICAL"
  },
  "skip_rate": {
    "shap_contribution": +0.15,
    "business_meaning": "High skip rate indicates content mismatch",
    "lever": "Improve recommendations algorithm",
    "lever_strength": "HIGH"
  },
  "listening_time": {
    "shap_contribution": -0.12,
    "business_meaning": "Higher engagement = lower churn risk",
    "lever": "Drive engagement via challenges, playlists",
    "lever_strength": "MEDIUM"
  }
}
```

---

## 5. Error Codes & Definitions

| Code | HTTP | Description |
|------|------|-------------|
| USER_NOT_FOUND | 404 | User ID not found in dataset |
| INVALID_REQUEST | 400 | Request format is invalid |
| INSUFFICIENT_DATA | 400 | Not enough data to generate explanation |
| MODEL_NOT_LOADED | 500 | Prediction model not available |
| EXPLANATION_TIMEOUT | 504 | Explanation generation exceeded timeout |
| AUTHENTICATION_FAILED | 401 | Invalid/missing authentication |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |

---

## 6. Implementation Requirements

### 6.1 Libraries & Dependencies
- `shap`: SHAP values computation
- `lime`: LIME explanations (fallback)
- `numpy`, `pandas`: Data manipulation
- `sklearn`: Model utilities
- `fastapi`: REST API framework
- `pydantic`: Request validation
- `redis`: Caching explanations

### 6.2 Performance Requirements
- Single explanation: <500ms
- Batch (100 users): <30s
- Explanation caching: 24 hours
- API uptime: 99.5%

### 6.3 Quality Requirements
- Feature attribution sum ≈ model output
- SHAP value consistency: stability score >0.80
- Text explanation clarity: human readability score >0.85
- Actionability: >90% of explanations suggest actions

---

## 7. Version History
| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-26 | Initial API specification |

