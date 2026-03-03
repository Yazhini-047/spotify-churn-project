"""
CHATBOT CONVERSATION FLOWS & DIALOG MANAGEMENT
================================================
Handles conversational logic, intent detection, and multi-turn interactions
for the Spotify Churn Prediction chatbot.

Features:
- Multi-turn conversation support
- Intent classification
- Context awareness
- Playbook recommendation flow
- Offer personalization
- Session state management

Author: Role 3 Backend Developer
Date: 2026-02-26
"""

from enum import Enum
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import re
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class ConversationIntent(str, Enum):
    """User intent classification"""
    EXPLAIN_CHURN = "explain_churn"
    GET_RECOMMENDATIONS = "get_recommendations"
    EXECUTE_ACTION = "execute_action"
    GENERAL_HELP = "general_help"
    PRICING_INQUIRY = "pricing_inquiry"
    CANCEL_SUBSCRIPTION = "cancel_subscription"
    TECH_SUPPORT = "tech_support"
    FEEDBACK = "feedback"
    UNKNOWN = "unknown"


class ConversationPhase(str, Enum):
    """Chat conversation phase"""
    GREETING = "greeting"
    CONTEXT_GATHERING = "context_gathering"
    EXPLANATION = "explanation"
    RECOMMENDATION = "recommendation"
    OFFER_PRESENTATION = "offer_presentation"
    ACTION_EXECUTION = "action_execution"
    CLOSING = "closing"


class Sentiment(str, Enum):
    """Detected sentiment"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class ConversationContext:
    """Maintains conversation state"""
    user_id: str
    session_id: str
    created_at: datetime
    last_interaction: datetime
    
    # User profile
    churn_probability: Optional[float] = None
    risk_segment: Optional[str] = None
    subscription_type: Optional[str] = None
    
    # Conversation state
    phase: ConversationPhase = ConversationPhase.GREETING
    turn_count: int = 0
    intent_history: List[ConversationIntent] = field(default_factory=list)
    message_history: List[Dict[str, str]] = field(default_factory=list)
    
    # Offers shown
    offers_presented: List[str] = field(default_factory=list)
    playbook_recommended: Optional[str] = None
    playbook_accepted: bool = False
    
    # Sentiment tracking
    sentiment_history: List[Sentiment] = field(default_factory=list)
    
    def update_last_interaction(self):
        """Update last interaction timestamp"""
        self.last_interaction = datetime.utcnow()
    
    def add_message(self, role: str, content: str):
        """Add message to history"""
        self.message_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.turn_count += 1
    
    def add_intent(self, intent: ConversationIntent):
        """Add intent to history"""
        self.intent_history.append(intent)
    
    def add_sentiment(self, sentiment: Sentiment):
        """Add sentiment to history"""
        self.sentiment_history.append(sentiment)


@dataclass
class ChatResponse:
    """Response structure for chatbot"""
    content: str
    intent: ConversationIntent
    sentiment: Sentiment
    suggested_actions: List[Dict[str, Any]] = field(default_factory=list)
    offers: List[Dict[str, Any]] = field(default_factory=list)
    phase: ConversationPhase = ConversationPhase.GREETING


# ============================================================================
# INTENT DETECTION
# ============================================================================

class IntentClassifier:
    """Classifies user intent from input text"""
    
    INTENT_KEYWORDS = {
        ConversationIntent.EXPLAIN_CHURN: [
            "why", "churn", "leave", "cancel", "risk", "probability",
            "churn rate", "likelihood", "likely", "going to churn",
            "will i churn", "should i worry", "factors"
        ],
        ConversationIntent.GET_RECOMMENDATIONS: [
            "recommend", "suggest", "offer", "what can you offer",
            "what do i get", "how can you help", "what should i do",
            "solution", "fix", "improve", "better"
        ],
        ConversationIntent.EXECUTE_ACTION: [
            "yes", "okay", "ok", "sure", "agree", "accept", "sign up",
            "activate", "start", "enable", "apply", "claim"
        ],
        ConversationIntent.PRICING_INQUIRY: [
            "price", "cost", "fee", "payment", "billing", "how much",
            "expensive", "premium", "subscription"
        ],
        ConversationIntent.CANCEL_SUBSCRIPTION: [
            "cancel", "delete", "remove", "unsubscribe", "quit", "stop",
            "terminate", "discontinue"
        ],
        ConversationIntent.TECH_SUPPORT: [
            "bug", "error", "issue", "problem", "broken", "not working",
            "crash", "slow", "technical"
        ],
        ConversationIntent.FEEDBACK: [
            "feedback", "comment", "suggestion", "review", "opinion",
            "like", "dislike", "experience"
        ],
        ConversationIntent.GENERAL_HELP: [
            "help", "support", "guide", "how to", "tutorial", "explain",
            "what is", "tell me"
        ]
    }
    
    @staticmethod
    def classify(user_input: str) -> Tuple[ConversationIntent, float]:
        """
        Classify user input intent.
        Returns intent and confidence score.
        """
        user_input_lower = user_input.lower()
        intent_scores = {}
        
        # Score each intent
        for intent, keywords in IntentClassifier.INTENT_KEYWORDS.items():
            score = sum(
                1 for keyword in keywords
                if keyword in user_input_lower
            )
            if score > 0:
                intent_scores[intent] = score
        
        if not intent_scores:
            return ConversationIntent.UNKNOWN, 0.0
        
        # Get highest scoring intent
        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = min(intent_scores[best_intent] / 3.0, 1.0)
        
        return best_intent, confidence
    
    @staticmethod
    def detect_sentiment(user_input: str) -> Sentiment:
        """
        Simple sentiment detection based on keywords.
        """
        positive_words = {"good", "great", "excellent", "love", "amazing", "happy", "yes"}
        negative_words = {"bad", "terrible", "hate", "angry", "frustrated", "no", "don't"}
        frustrated_words = {"angry", "frustrated", "annoyed", "upset", "mad"}
        
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in frustrated_words):
            return Sentiment.FRUSTRATED
        elif any(word in user_lower for word in positive_words):
            return Sentiment.POSITIVE
        elif any(word in user_lower for word in negative_words):
            return Sentiment.NEGATIVE
        else:
            return Sentiment.NEUTRAL


# ============================================================================
# RESPONSE GENERATION
# ============================================================================

class ResponseGenerator:
    """Generates contextual chatbot responses"""
    
    # Response templates by phase and intent
    TEMPLATES = {
        ConversationPhase.GREETING: {
            "content": "👋 Hi {user_name}! I'm your Spotify support assistant. I'm here to help you get the most out of your subscription. How can I help you today?",
            "suggested_actions": [
                {"type": "explain_churn", "label": "Why might I churn?"},
                {"type": "get_offers", "label": "Show me personalized offers"}
            ]
        },
        
        ConversationPhase.EXPLANATION: {
            "high_risk": {
                "content": "I've analyzed your account and found some factors that might lead to churn: {factors}. Would you like personalized recommendations?",
                "offers": [{"type": "premium_trial", "label": "1-month Free Premium Trial"}]
            },
            "medium_risk": {
                "content": "Your engagement is moderate. {factors}. We have some suggestions to enhance your experience.",
                "offers": [{"type": "discount", "label": "20% off next purchase"}]
            },
            "low_risk": {
                "content": "You seem to be enjoying Spotify! Here's what we love about your profile: {factors}. Keep it up! 🎵"
            }
        },
        
        ConversationPhase.RECOMMENDATION: {
            "content": "Based on your profile, here are my top recommendations:\n\n{recommendations}\n\nWould you like to activate any of these?",
            "suggested_actions": [
                {"type": "activate", "label": "Activate recommendation"},
                {"type": "see_more", "label": "Show more options"}
            ]
        },
        
        ConversationPhase.OFFER_PRESENTATION: {
            "premium_trial": {
                "content": "✨ Exclusive Offer: Get 1 month of Premium absolutely free! You'll unlock:\n - Ad-free listening\n - Offline downloads\n - Higher audio quality (320kbps)\n\nStart your free trial?",
                "actions": [{"type": "accept", "label": "Yes, activate"}, {"type": "decline", "label": "Not now"}]
            },
            "discount": {
                "content": "🎁 Limited Time Offer: Get 30% off your first month of Premium!\n\nSave now?",
                "actions": [{"type": "accept", "label": "Claim offer"}, {"type": "decline", "label": "Maybe later"}]
            }
        },
        
        ConversationPhase.CLOSING: {
            "content": "Thanks for chatting with me today! I've activated your offer. Check your email for the details. Is there anything else I can help with?"
        }
    }
    
    @staticmethod
    def generate_response(
        context: ConversationContext,
        user_intent: ConversationIntent,
        sentiment: Sentiment
    ) -> ChatResponse:
        """
        Generate contextual response based on conversation state.
        """
        # Determine next phase
        next_phase = ResponseGenerator._determine_next_phase(context, user_intent, sentiment)
        context.phase = next_phase
        
        # Generate response content
        if next_phase == ConversationPhase.GREETING and context.turn_count == 1:
            content = f"👋 Hi! I'm your Spotify support assistant. How can I help you today?"
            suggested_actions = [
                {"type": "explain_churn", "label": "Why might I churn?"},
                {"type": "get_offers", "label": "Show me offers"}
            ]
            offers = []
        
        elif next_phase == ConversationPhase.EXPLANATION:
            if context.churn_probability and context.churn_probability > 0.67:
                risk_level = "high risk"
                factors = "low Premium conversion and limited engagement"
            else:
                risk_level = "moderate"
                factors = "adequate engagement but growth opportunities"
            
            content = f"I analyzed your account and identified some factors: {factors}. Would you like personalized recommendations?"
            suggested_actions = [{"type": "show_recs", "label": "Show recommendations"}]
            offers = [{"type": "premium_trial", "label": "1-month Free Trial"}]
        
        elif next_phase == ConversationPhase.RECOMMENDATION:
            content = "Based on your profile, here are my top recommendations:\n\n1. 🎵 Upgrade to Premium - Ad-free, offline, HQ audio\n2. 🎁 Premium Family Plan - Share with family members\n3. 📻 Create personalized playlists\n\nWhich interests you?"
            suggested_actions = [{"type": "activate", "label": "Activate"}]
            offers = []
        
        elif next_phase == ConversationPhase.OFFER_PRESENTATION:
            content = "✨ Exclusive Offer: 1 month Premium free!\n- Ad-free listening\n- Offline downloads\n- Higher quality audio\n\nActivate now?"
            suggested_actions = [{"type": "accept", "label": "Yes"}, {"type": "decline", "label": "No thanks"}]
            offers = [{"type": "premium_trial", "label": "Activate Free Trial"}]
        
        elif next_phase == ConversationPhase.ACTION_EXECUTION:
            content = "Great! I've activated your offer. 🎉 Check your email for details. Is there anything else I can help?"
            suggested_actions = []
            offers = []
        
        else:  # CLOSING or GENERAL_HELP
            content = "Is there anything else I can help you with? I'm here to support your Spotify experience!"
            suggested_actions = [
                {"type": "technical_help", "label": "Technical help"},
                {"type": "feedback", "label": "Share feedback"}
            ]
            offers = []
        
        return ChatResponse(
            content=content,
            intent=user_intent,
            sentiment=sentiment,
            suggested_actions=suggested_actions,
            offers=offers,
            phase=next_phase
        )
    
    @staticmethod
    def _determine_next_phase(
        context: ConversationContext,
        intent: ConversationIntent,
        sentiment: Sentiment
    ) -> ConversationPhase:
        """Determine the next conversation phase"""
        
        # Handle frustrated sentiment
        if sentiment == Sentiment.FRUSTRATED:
            return ConversationPhase.TECH_SUPPORT
        
        # Flow logic
        if intent == ConversationIntent.EXPLAIN_CHURN:
            return ConversationPhase.EXPLANATION
        
        elif intent == ConversationIntent.GET_RECOMMENDATIONS:
            return ConversationPhase.RECOMMENDATION if context.phase != ConversationPhase.RECOMMENDATION else ConversationPhase.OFFER_PRESENTATION
        
        elif intent == ConversationIntent.EXECUTE_ACTION:
            if context.phase == ConversationPhase.OFFER_PRESENTATION:
                return ConversationPhase.ACTION_EXECUTION
            else:
                return ConversationPhase.RECOMMENDATION
        
        elif intent == ConversationIntent.GENERAL_HELP:
            return ConversationPhase.CONTEXT_GATHERING
        
        else:
            return context.phase


# ============================================================================
# CHATBOT CONVERSATION MANAGER
# ============================================================================

class ChatbotManager:
    """Main chatbot manager handling multi-turn conversations"""
    
    def __init__(self):
        self.sessions: Dict[str, ConversationContext] = {}
        self.intent_classifier = IntentClassifier()
        self.response_generator = ResponseGenerator()
    
    def get_or_create_session(
        self,
        user_id: str,
        session_id: str,
        churn_probability: Optional[float] = None
    ) -> ConversationContext:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            context = ConversationContext(
                user_id=user_id,
                session_id=session_id,
                created_at=datetime.utcnow(),
                last_interaction=datetime.utcnow(),
                churn_probability=churn_probability,
                risk_segment=self._get_risk_segment(churn_probability)
            )
            self.sessions[session_id] = context
            logger.info(f"Created new session {session_id} for user {user_id}")
        
        return self.sessions[session_id]
    
    def process_message(
        self,
        session_id: str,
        user_message: str
    ) -> ChatResponse:
        """
        Process user message and generate response.
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        context = self.sessions[session_id]
        context.update_last_interaction()
        
        # Add user message to history
        context.add_message("user", user_message)
        
        # Classify intent
        intent, confidence = self.intent_classifier.classify(user_message)
        context.add_intent(intent)
        
        # Detect sentiment
        sentiment = self.intent_classifier.detect_sentiment(user_message)
        context.add_sentiment(sentiment)
        
        logger.info(f"Session {session_id}: Intent={intent}, Sentiment={sentiment}, Confidence={confidence:.2f}")
        
        # Generate response
        response = self.response_generator.generate_response(context, intent, sentiment)
        
        # Add assistant message to history
        context.add_message("assistant", response.content)
        
        return response
    
    @staticmethod
    def _get_risk_segment(churn_probability: Optional[float]) -> Optional[str]:
        """Get risk segment from churn probability"""
        if churn_probability is None:
            return None
        if churn_probability < 0.33:
            return "low_risk"
        elif churn_probability < 0.67:
            return "medium_risk"
        else:
            return "high_risk"
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get conversation summary"""
        if session_id not in self.sessions:
            return {}
        
        context = self.sessions[session_id]
        return {
            "user_id": context.user_id,
            "session_id": session_id,
            "turn_count": context.turn_count,
            "duration_seconds": (context.last_interaction - context.created_at).total_seconds(),
            "intent_history": [intent.value for intent in context.intent_history],
            "sentiment_progression": [sent.value for sent in context.sentiment_history],
            "offers_presented": context.offers_presented,
            "playbook_recommended": context.playbook_recommended,
            "playbook_accepted": context.playbook_accepted
        }


# ============================================================================
# MOCK CHAT TRANSCRIPTS (FOR TESTING & DOCUMENTATION)
# ============================================================================

MOCK_TRANSCRIPTS = {
    "high_risk_conversion": {
        "scenario": "High-risk free user likely to churn",
        "transcript": [
            {
                "turn": 1,
                "user": "I'm thinking about canceling my Spotify account",
                "assistant": "Oh no! I'm sorry to hear that. Can I help you find a better experience with Spotify? What's making you consider canceling?",
                "intent": "CANCEL_SUBSCRIPTION",
                "sentiment": "NEGATIVE"
            },
            {
                "turn": 2,
                "user": "The ads are too much and I can't find good music",
                "assistant": "I understand! Ads can be annoying on the free plan. Here's the good news: Premium users get ad-free listening plus offline downloads. Plus, we have ML-powered recommendations that improve over time. How about trying Premium free for a month?",
                "intent": "PRICING_INQUIRY",
                "sentiment": "NEGATIVE",
                "offers": ["1-month free premium trial"]
            },
            {
                "turn": 3,
                "user": "Really? Free for the first month?",
                "assistant": "✨ Yes! You get 30 days of Premium completely free. No credit card needed. After that, it's just $12.99/month. But you can cancel anytime. Want to start your trial now?",
                "intent": "GET_RECOMMENDATIONS",
                "sentiment": "NEUTRAL"
            },
            {
                "turn": 4,
                "user": "Okay, let's do it!",
                "assistant": "🎉 Awesome! I've activated your 1-month Premium trial. You'll get an email confirmation shortly. Enjoy ad-free listening, offline downloads, and our best music recommendations. Is there anything else I can help with?",
                "intent": "EXECUTE_ACTION",
                "sentiment": "POSITIVE"
            }
        ]
    },
    
    "medium_risk_engagement": {
        "scenario": "Medium-risk user with moderate engagement",
        "transcript": [
            {
                "turn": 1,
                "user": "I'm not using Spotify as much lately",
                "assistant": "I see that your engagement has dropped recently. I'd love to help you rediscover music you love! What's changed?",
                "intent": "GENERAL_HELP",
                "sentiment": "NEUTRAL"
            },
            {
                "turn": 2,
                "user": "Just busy with work, and something's not quite right",
                "assistant": "Understood! Let me share some insights: You're streaming less, but when you do, you engage with high-quality music. Here's how we can improve your experience: 1) Personalized Discover Weekly playlists, 2) A family plan to share with friends, 3) Premium for offline listening during your commute.",
                "intent": "GET_RECOMMENDATIONS",
                "sentiment": "NEUTRAL",
                "offers": ["20% discount premium", "Family plan offer"]
            },
            {
                "turn": 3,
                "user": "Family plan sounds good, but I need to think about it",
                "assistant": "That makes sense! Here's a special offer: 20% off a 3-month Premium gift card. This is perfect to test Premium while being on a family plan offer. I'll send you the details via email. Check your inbox! 📧",
                "intent": "EXECUTE_ACTION",
                "sentiment": "POSITIVE"
            }
        ]
    },
    
    "technical_support": {
        "scenario": "User with technical issues",
        "transcript": [
            {
                "turn": 1,
                "user": "The app keeps crashing when I try to play songs",
                "assistant": "I'm sorry you're experiencing issues! That's frustrating. Let me help troubleshoot. Can you tell me which device and OS version you're using?",
                "intent": "TECH_SUPPORT",
                "sentiment": "FRUSTRATED"
            },
            {
                "turn": 2,
                "user": "iPhone 14, latest iOS",
                "assistant": "Thanks! Let's try these steps: 1) Force quit the app 2) Clear app cache 3) Reinstall if needed. If issues persist, contact our technical support team directly. I'm escalating your case now. You'll hear from them within 2 hours.",
                "intent": "TECH_SUPPORT",
                "sentiment": "FRUSTRATED",
                "actions": ["escalate_support", "priority_queue"]
            }
        ]
    }
}


if __name__ == "__main__":
    # Test the chatbot
    chatbot = ChatbotManager()
    
    print("\n" + "="*60)
    print("CHATBOT TEST - HIGH RISK CONVERSION SCENARIO")
    print("="*60 + "\n")
    
    session = chatbot.get_or_create_session(
        user_id="user_123",
        session_id="session_abc",
        churn_probability=0.75
    )
    
    test_messages = [
        "Why might I churn?",
        "Can you show me what Premium offers?",
        "I'm interested in trying Premium",
        "Yes, let's do it!"
    ]
    
    for msg in test_messages:
        print(f"👤 User: {msg}")
        response = chatbot.process_message("session_abc", msg)
        print(f"🤖 Assistant: {response.content}")
        print(f"   Intent: {response.intent.value}")
        print(f"   Phase: {response.phase.value}\n")
    
    print("\nSession Summary:")
    print(json.dumps(chatbot.get_session_summary("session_abc"), indent=2, default=str))
    