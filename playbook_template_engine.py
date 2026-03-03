"""
PLAYBOOK TEMPLATE ENGINE
=========================
Implements actionable playbook templates based on user explanations and risk profiles.
Templates are rendered dynamically based on user data and business rules.
"""

import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random

# ============================================================================
# 1. PLAYBOOK TEMPLATE SYSTEM
# ============================================================================

class PlaybookTemplateEngine:
    """
    Renders personalized playbook actions based on user context.
    """
    
    def __init__(self, playbook_ruleset: Dict):
        """
        Initialize with playbook ruleset.
        
        Args:
            playbook_ruleset: Dictionary loaded from 02_PLAYBOOK_RULESET.json
        """
        self.ruleset = playbook_ruleset
        self.playbooks = {pb['playbook_id']: pb for pb in playbook_ruleset['playbooks']}
    
    def recommend_playbooks(self, user_data: Dict, user_explanation: Dict) -> List[Dict]:
        """
        Recommend applicable playbooks for a user.
        
        Args:
            user_data: User's feature data
            user_explanation: Explanation output from SHAP engine
            
        Returns:
            List of recommended playbooks with personalized actions
        """
        churn_prob = user_explanation['prediction']['churn_probability']
        risk_segment = user_explanation['prediction']['risk_segment']
        
        recommendations = []
        
        # Match playbooks to user profile
        for playbook_id, playbook in self.playbooks.items():
            if self._matches_criteria(user_data, playbook['segment_criteria']):
                # Personalize the playbook
                personalized = self._personalize_playbook(
                    playbook, user_data, user_explanation
                )
                recommendations.append(personalized)
        
        # Sort by priority and expected impact
        recommendations.sort(
            key=lambda x: x.get('priority', 0),
            reverse=True
        )
        
        return recommendations[:3]  # Top 3 recommendations
    
    def _matches_criteria(self, user_data: Dict, criteria: Dict) -> bool:
        """Check if user matches playbook criteria."""
        churn_prob = user_data.get('churn_probability', 0)
        
        # Probability range
        if 'churn_probability_min' in criteria:
            if churn_prob < criteria['churn_probability_min']:
                return False
        if 'churn_probability_max' in criteria:
            if churn_prob > criteria['churn_probability_max']:
                return False
        
        # Ads threshold
        if 'ads_listened_per_week_min' in criteria:
            if user_data.get('ads_listened_per_week', 0) < criteria['ads_listened_per_week_min']:
                return False
        
        # Skip rate threshold
        if 'skip_rate_min' in criteria:
            if user_data.get('skip_rate', 0) < criteria['skip_rate_min']:
                return False
        
        # Listening time threshold
        if 'listening_time_max' in criteria:
            if user_data.get('listening_time', 0) > criteria['listening_time_max']:
                return False
        
        # Subscription type
        if 'subscription_type' in criteria:
            if user_data.get('subscription_type') != criteria['subscription_type']:
                return False
        
        return True
    
    def _personalize_playbook(self, playbook: Dict, user_data: Dict, 
                             user_explanation: Dict) -> Dict:
        """
        Personalize playbook by rendering templates with user-specific data.
        """
        personalized = playbook.copy()
        personalized_actions = []
        
        for action in playbook.get('actions', []):
            personalized_action = self._render_action_template(
                action, user_data, user_explanation
            )
            personalized_actions.append(personalized_action)
        
        personalized['actions'] = personalized_actions
        return personalized
    
    def _render_action_template(self, action: Dict, user_data: Dict,
                               user_explanation: Dict) -> Dict:
        """
        Render an action template with user-specific values.
        """
        rendered = action.copy()
        
        # Get template content
        template_id = action.get('template_id')
        if template_id:
            template_content = self._get_template(template_id, user_data, user_explanation)
            rendered['rendered_content'] = template_content
        
        # Calculate timing
        if action.get('timing') == 'immediate':
            rendered['scheduled_time'] = datetime.now().isoformat()
        elif action.get('timing') == 'day1':
            rendered['scheduled_time'] = (datetime.now() + timedelta(days=1)).isoformat()
        elif action.get('timing') == 'day3_if_not_converted':
            rendered['scheduled_time'] = (datetime.now() + timedelta(days=3)).isoformat()
        
        return rendered
    
    # ========================================================================
    # 2. TEMPLATE SYSTEM
    # ========================================================================
    
    def _get_template(self, template_id: str, user_data: Dict, 
                     user_explanation: Dict) -> Dict:
        """
        Get and render template content.
        """
        templates = {
            'TEMPLATE_PREMIUM_TRIAL_V1': self._template_premium_trial,
            'TEMPLATE_3MONTH_DISCOUNT_V1': self._template_3month_discount,
            'TEMPLATE_ADFREE_TRIAL_WEEK_V1': self._template_adfree_trial,
            'TEMPLATE_MUSIC_PREF_SURVEY_V1': self._template_music_survey,
            'TEMPLATE_WINBACK_EMAIL_V1': self._template_winback_email,
            'TEMPLATE_LISTEN_CHALLENGE_V1': self._template_listen_challenge,
            'TEMPLATE_LAST_EFFORT_DISCOUNT_V1': self._template_last_effort,
            'TEMPLATE_PERSONAL_MESSAGE_V1': self._template_personal_message,
            'TEMPLATE_WEEKLY_FEEDBACK_V1': self._template_weekly_feedback,
        }
        
        renderer = templates.get(template_id)
        if renderer:
            return renderer(user_data, user_explanation)
        return {}
    
    def _template_premium_trial(self, user_data: Dict, explanation: Dict) -> Dict:
        """Premium trial offer template."""
        return {
            'subject': f"🎵 Upgrade to Premium Free for One Month",
            'preview': "No ads, unlimited skips, and offline downloads",
            'body': f"""
Hi there!

We noticed you love music but might be frustrated with ads. We have an offer!
Enjoy Premium completely FREE for 30 days:
• Zero interruptions (no ads)
• Unlimited skips
• Offline downloads
• High-quality audio

After 30 days, it's just $9.99/month. Cancel anytime - no commitment!

[Button: Start Your Free Month]

This offer expires in 7 days, so claim it now!

Best,
The Spotify Team
            """,
            'cta_text': 'Start Your Free Month',
            'cta_link': '/premium/trial?ref=churn_save',
            'sender': 'noreply@spotify.com',
            'color_scheme': 'green'
        }
    
    def _template_3month_discount(self, user_data: Dict, explanation: Dict) -> Dict:
        """3-month discount template."""
        return {
            'subject': "Last Chance: Just $4.97/month - We Really Want You to Hear This",
            'preview': "Limited time: 50% off Premium for 3 months",
            'body': f"""
We've been thinking about you...

One more thing before you go: Premium is just $4.97/month for 3 months (50% off).

That's just $14.97 total for 3 months of:
✓ No ads, ever
✓ Unlimited skips
✓ Offline downloads
✓ Premium sound quality

After 3 months, it's $9.99/month. You can cancel anytime.

[Button: Lock in $4.97/month]

This deal expires in 3 days.

Your music, your way,
Spotify
            """,
            'cta_text': 'Lock in $4.97/month',
            'cta_link': '/premium/3month-deal',
            'color_scheme': 'orange'
        }
    
    def _template_adfree_trial(self, user_data: Dict, explanation: Dict) -> Dict:
        """Ad-free trial template."""
        return {
            'in_app_title': 'Try Premium Free - One Week',
            'in_app_description': 'See what ad-free listening is really like.',
            'body': """
Ready to experience music without interruptions?

Get 7 days of Premium completely free:
🎧 Zero ads
🎵 Unlimited skips
📱 Take downloads offline

If you love it, Premium is $9.99/month. Don't love it? No charge.

[Button: Start Your Free Week]
            """,
            'button_text': 'Start Free 7-Day Trial',
            'cta_link': '/premium/7day-trial?ref=ad_reduction',
            'image_url': '/assets/adfree_trial_banner.png'
        }
    
    def _template_music_survey(self, user_data: Dict, explanation: Dict) -> Dict:
        """Music preference survey template."""
        return {
            'title': 'Help Us Understand Your Music Taste',
            'description': 'Quick 2-minute survey - Get a custom playlist!',
            'questions': [
                {
                    'id': 'q1',
                    'question': 'What\'s your favorite music genre?',
                    'type': 'multiple_choice',
                    'options': ['Pop', 'Rock', 'Hip-Hop', 'EDM', 'Classical', 'Other']
                },
                {
                    'id': 'q2',
                    'question': 'How do you usually listen to music?',
                    'type': 'multiple_choice',
                    'options': ['Focus', 'Workout', 'Party', 'Relaxation', 'Commute']
                },
                {
                    'id': 'q3',
                    'question': 'Any artists you\'re obsessed with?',
                    'type': 'text_input'
                }
            ],
            'reward': 'Get a personalized playlist crafted just for you!',
            'reward_details': '25 songs based on your answers. We promise you\'ll find at least 5 new favorites.'
        }
    
    def _template_winback_email(self, user_data: Dict, explanation: Dict) -> Dict:
        """Winback campaign template."""
        return {
            'subject': "🎵 Your Favorite Artists Just Released New Music",
            'preview': "Check out 10 new releases since you last visited",
            'body': f"""
Hey! We miss you!

Your favorite artists have been busy:
• Drake - 3 new tracks
• Taylor Swift - 2 new releases
• The Weeknd - New album (6 songs!)
... and 5 more from artists you love

[Button: See What You've Missed]

Come back and catch up on the latest hits. We've also updated your personalized recommendations!

See you on the other side,
Spotify
            """,
            'cta_text': 'See What You\'ve Missed',
            'cta_link': '/new-releases-for-you',
            'sender': 'noreply@spotify.com'
        }
    
    def _template_listen_challenge(self, user_data: Dict, explanation: Dict) -> Dict:
        """Listen challenge template."""
        return {
            'title': '7-Day Listen Challenge',
            'description': 'Discover 7 new artists. Earn exclusive badges!',
            'challenge_rules': [
                {
                    'day': 1,
                    'task': 'Listen to an artist you\'ve never heard before',
                    'reward': 'Bronze Explorer Badge'
                },
                {
                    'day': 2,
                    'task': 'Listen to a song from a different decade',
                    'reward': 'Time Traveler Badge'
                },
                {
                    'day': 3,
                    'task': 'Explore a playlist outside your favorite genre',
                    'reward': 'Genre Adventurer Badge'
                },
                {
                    'day': 7,
                    'task': 'Complete all 7 days',
                    'reward': 'Gold Listener Badge + Custom Playlist'
                }
            ],
            'total_reward': 'Featured on your profile + 1-week Premium trial',
            'call_to_action': 'Start Your Challenge'
        }
    
    def _template_last_effort(self, user_data: Dict, explanation: Dict) -> Dict:
        """Last-effort discount offer."""
        return {
            'subject': '🚨 URGENT: Unbelievable Offer - 70% Off (24 Hours Only)',
            'preview': '70% off Premium for 6 months - Expires tonight',
            'body': f"""
This is your last offer.

We don't want you to go. Here's what we can do:

70% OFF PREMIUM - 6 MONTHS
$17.97 total for 6 months
(That's just $2.99/month!)

✓ No ads ever
✓ Unlimited skips
✓ Offline downloads
✓ Premium sound quality
✓ Cancel anytime

After 6 months it's $9.99/month.

[Button: Claim Your 70% Discount]

⏰ This offer expires in 24 HOURS

If you leave, you'll miss out on this deal forever.

Last chance,
Spotify Team
            """,
            'cta_text': 'YES! Claim 70% Off Now',
            'cta_link': '/premium/last-chance-70off',
            'color_scheme': 'red',
            'urgency': 'high',
            'expiry_hours': 24
        }
    
    def _template_personal_message(self, user_data: Dict, explanation: Dict) -> Dict:
        """Personal message from product leader."""
        return {
            'subject': 'A Personal Message from Our Head of Product',
            'preview': 'We don\'t want you to leave. How can we help?',
            'body': f"""
Hi {user_data.get('user_name', 'there')},

I'm Sarah, Head of Product at Spotify.

I saw that you're thinking about leaving, and I wanted to reach out personally.

We build Spotify FOR people like you - people who love music. If we're not meeting your needs, I want to know why.

Is it:
- Too many ads? (We can fix that)
- Bad recommendations? (Help us improve)
- Missing features? (Tell us what would make it perfect)
- Budget? (We have options)

Reply to this email and let's talk. I read every response personally.

Whatever it takes to keep you with us.

Sincerely,
Sarah
Head of Product, Spotify

P.S. - Here's a special code for 50% off Premium: SAVEMUSIC50
            """,
            'sender_name': 'Sarah, Head of Product',
            'sender_title': 'Head of Product Experience',
            'tone': 'personal',
            'allow_reply': True
        }
    
    def _template_weekly_feedback(self, user_data: Dict, explanation: Dict) -> Dict:
        """Weekly feedback template."""
        return {
            'subject': '👂 Quick question: How are your recommendations?',
            'preview': 'Help us improve in just 2 clicks',
            'body': """
Quick question!

How are your Spotify recommendations this week?

[Poor] [Okay] [Good] [Excellent]

We adjust our algorithm based on your feedback, so this helps us get better!

Thanks,
Spotify
            """,
            'quick_feedback': True,
            'one_click_options': ['Poor', 'Okay', 'Good', 'Excellent']
        }


# ============================================================================
# 3. PLAYBOOK EXECUTION ENGINE
# ============================================================================

class PlaybookExecutionEngine:
    """
    Executes recommended playbooks (simulates action delivery).
    """
    
    def __init__(self, template_engine: PlaybookTemplateEngine):
        self.template_engine = template_engine
        self.execution_log = []
    
    def execute_playbook(self, playbook: Dict, user_id: str) -> Dict:
        """
        Execute a playbook for a user.
        
        Returns execution log with status of each action.
        """
        execution_record = {
            'playbook_id': playbook['playbook_id'],
            'user_id': user_id,
            'start_time': datetime.now().isoformat(),
            'actions_executed': [],
            'total_expected_impact': playbook.get('estimated_impact', {})
        }
        
        for action in playbook.get('actions', []):
            result = self._execute_action(action, user_id)
            execution_record['actions_executed'].append(result)
        
        execution_record['end_time'] = datetime.now().isoformat()
        self.execution_log.append(execution_record)
        
        return execution_record
    
    def _execute_action(self, action: Dict, user_id: str) -> Dict:
        """
        Execute a single action.
        """
        result = {
            'action_id': action.get('action_id'),
            'action_name': action.get('action_name'),
            'channel': action.get('channel'),
            'status': 'executed',
            'timestamp': datetime.now().isoformat(),
            'details': {
                'user_id': user_id,
                'scheduled_time': action.get('scheduled_time'),
                'rendered_content': action.get('rendered_content', {})
            }
        }
        
        return result


# ============================================================================
# 4. MAIN DEMONSTRATION
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("PLAYBOOK TEMPLATE ENGINE - DEMONSTRATION")
    print("=" * 80)
    
    # Load playbook ruleset
    with open('02_PLAYBOOK_RULESET.json', 'r') as f:
        ruleset = json.load(f)
    
    # Initialize engine
    template_engine = PlaybookTemplateEngine(ruleset['playbook_catalog'])
    
    # Create sample user
    sample_user = {
        'user_id': 'user_12345',
        'subscription_type': 'Free',
        'listening_time': 25,
        'ads_listened_per_week': 45,
        'skip_rate': 0.72,
        'churn_probability': 0.82
    }
    
    # Create sample explanation
    sample_explanation = {
        'prediction': {
            'churn_probability': 0.82,
            'risk_segment': 'high_risk',
            'prediction_label': 1
        }
    }
    
    print("\nRecommending playbooks for sample user...")
    print(f"User Churn Probability: {sample_user['churn_probability']:.1%}\n")
    
    recommendations = template_engine.recommend_playbooks(sample_user, sample_explanation)
    
    for i, playbook in enumerate(recommendations, 1):
        print(f"\n📋 Playbook {i}: {playbook['playbook_name']}")
        print(f"   ID: {playbook['playbook_id']}")
        print(f"   Priority: {playbook['priority']}/5")
        print(f"   Expected Impact: {playbook.get('estimated_impact', {})}")
        print(f"   Actions: {len(playbook.get('actions', []))}")
    
    print("\n" + "=" * 80)
    print("✅ Playbook Template Engine Ready!")
    print("=" * 80)
