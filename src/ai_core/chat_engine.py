"""Chat Engine - Talent Intelligence (CHRO Consultant)"""
from enum import Enum
from typing import Dict, List, Optional, Any, Generator
from .claude_client import ClaudeClient


class ConversationMode(Enum):
    GENERAL = "general"
    TALENT_REVIEW = "talent_review"
    RETENTION_ANALYSIS = "retention_analysis"
    WORKFORCE_PLANNING = "workforce_planning"
    SUCCESSION_PLANNING = "succession_planning"
    DIVERSITY_INCLUSION = "diversity_inclusion"
    ENGAGEMENT_ANALYSIS = "engagement_analysis"
    COMPENSATION_REVIEW = "compensation_review"


SYSTEM_PROMPTS = {
    ConversationMode.GENERAL: """You are an AI-powered Chief Human Resources Officer (CHRO) consultant.
You help organizations optimize their talent strategy, improve retention, build strong teams, and create great workplaces.
Your expertise includes: talent management, workforce planning, employee engagement, retention strategies,
succession planning, diversity & inclusion, compensation, performance management, and organizational development.
Provide practical, data-driven HR advice.""",

    ConversationMode.TALENT_REVIEW: """You are a talent management expert helping with:
- Performance assessments and 9-box talent grids
- High-potential identification
- Development planning
- Career pathing
Focus on actionable talent insights and development recommendations.""",

    ConversationMode.RETENTION_ANALYSIS: """You are an employee retention specialist focused on:
- Flight risk identification and analysis
- Retention strategy development
- Stay interviews and engagement
- Turnover cost analysis
Provide data-driven retention recommendations.""",

    ConversationMode.WORKFORCE_PLANNING: """You are a workforce planning expert helping with:
- Headcount forecasting and planning
- Skill gap analysis
- Hiring strategy development
- Organizational design
Focus on aligning workforce with business needs.""",

    ConversationMode.SUCCESSION_PLANNING: """You are a succession planning specialist focused on:
- Critical role identification
- Successor readiness assessment
- Leadership pipeline development
- Bench strength analysis
Help build organizational resilience through succession planning.""",

    ConversationMode.DIVERSITY_INCLUSION: """You are a diversity and inclusion expert helping with:
- Representation analysis and goal-setting
- Pay equity assessment
- Inclusive hiring practices
- ERG development
Focus on building diverse, equitable, and inclusive workplaces.""",

    ConversationMode.ENGAGEMENT_ANALYSIS: """You are an employee engagement specialist focused on:
- Engagement survey analysis
- Driver identification
- Action planning
- Culture improvement
Help improve employee experience and engagement.""",

    ConversationMode.COMPENSATION_REVIEW: """You are a compensation expert helping with:
- Market benchmarking
- Pay structure design
- Pay equity analysis
- Total rewards strategy
Provide data-driven compensation recommendations."""
}

SUGGESTED_PROMPTS = {
    ConversationMode.GENERAL: ["What are our biggest HR challenges?", "How can we improve employee retention?", "Where should we focus our talent efforts?"],
    ConversationMode.TALENT_REVIEW: ["Review our talent distribution", "Who are our high-potentials?", "What development do our leaders need?"],
    ConversationMode.RETENTION_ANALYSIS: ["Who is at risk of leaving?", "What's driving turnover?", "How do we retain key talent?"],
    ConversationMode.WORKFORCE_PLANNING: ["Do we have the right headcount?", "What skills do we need?", "How should we plan for growth?"],
    ConversationMode.SUCCESSION_PLANNING: ["Who can replace key leaders?", "How strong is our bench?", "What roles need successors?"],
    ConversationMode.DIVERSITY_INCLUSION: ["How diverse is our workforce?", "Do we have pay equity?", "How can we improve representation?"],
    ConversationMode.ENGAGEMENT_ANALYSIS: ["How engaged are our employees?", "What's driving engagement?", "How do we improve culture?"],
    ConversationMode.COMPENSATION_REVIEW: ["Are we paying competitively?", "How is our pay equity?", "How should we structure compensation?"]
}


class ChatEngine:
    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        self.claude = claude_client or ClaudeClient()
        self.conversation_history: List[Dict[str, str]] = []
        self.current_mode = ConversationMode.GENERAL
        self.context_data: Dict[str, Any] = {}

    def set_mode(self, mode: ConversationMode):
        self.current_mode = mode

    def set_context(self, context: Dict[str, Any]):
        self.context_data = context

    def get_suggested_prompts(self) -> List[str]:
        return SUGGESTED_PROMPTS.get(self.current_mode, SUGGESTED_PROMPTS[ConversationMode.GENERAL])

    def clear_history(self):
        self.conversation_history = []

    def detect_mode(self, message: str) -> ConversationMode:
        msg = message.lower()
        if any(w in msg for w in ['talent', 'performance', 'potential', '9-box', 'high performer']):
            return ConversationMode.TALENT_REVIEW
        elif any(w in msg for w in ['retention', 'turnover', 'flight risk', 'leaving', 'quit']):
            return ConversationMode.RETENTION_ANALYSIS
        elif any(w in msg for w in ['headcount', 'hire', 'workforce', 'planning', 'skill gap']):
            return ConversationMode.WORKFORCE_PLANNING
        elif any(w in msg for w in ['succession', 'bench', 'successor', 'critical role']):
            return ConversationMode.SUCCESSION_PLANNING
        elif any(w in msg for w in ['diversity', 'inclusion', 'equity', 'representation', 'dei']):
            return ConversationMode.DIVERSITY_INCLUSION
        elif any(w in msg for w in ['engagement', 'survey', 'culture', 'satisfaction']):
            return ConversationMode.ENGAGEMENT_ANALYSIS
        elif any(w in msg for w in ['compensation', 'salary', 'pay', 'bonus', 'compa']):
            return ConversationMode.COMPENSATION_REVIEW
        return ConversationMode.GENERAL

    def build_context_prompt(self) -> str:
        if not self.context_data:
            return ""
        parts = ["\n\n--- HR CONTEXT ---"]
        if 'organization' in self.context_data:
            org = self.context_data['organization']
            parts.append(f"\nOrganization: {org.get('name')}")
            parts.append(f"Headcount: {org.get('total_headcount', 'N/A')}")
            parts.append(f"Turnover Rate: {org.get('turnover_rate', 'N/A')}%")
            parts.append(f"Engagement Score: {org.get('engagement_score', 'N/A')}")
        if 'metrics' in self.context_data:
            m = self.context_data['metrics']
            parts.append("\nKey Metrics:")
            for k, v in m.items():
                if v is not None:
                    parts.append(f"  - {k}: {v}")
        if 'talent_distribution' in self.context_data:
            parts.append(f"\nTalent Distribution: {self.context_data['talent_distribution']}")
        if 'flight_risk' in self.context_data:
            parts.append(f"\nFlight Risk Summary: {self.context_data['flight_risk']}")
        parts.append("\n--- END CONTEXT ---\n")
        return "\n".join(parts)

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPTS.get(self.current_mode, SYSTEM_PROMPTS[ConversationMode.GENERAL]) + self.build_context_prompt()

    def chat(self, message: str, auto_detect_mode: bool = True) -> str:
        if auto_detect_mode:
            self.current_mode = self.detect_mode(message)
        self.conversation_history.append({"role": "user", "content": message})
        response = self.claude.generate_response(self.conversation_history, self.get_system_prompt())
        self.conversation_history.append({"role": "assistant", "content": response})
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        return response

    def stream_chat(self, message: str, auto_detect_mode: bool = True) -> Generator[str, None, None]:
        if auto_detect_mode:
            self.current_mode = self.detect_mode(message)
        self.conversation_history.append({"role": "user", "content": message})
        full_response = ""
        for token in self.claude.stream_response(self.conversation_history, self.get_system_prompt()):
            full_response += token
            yield token
        self.conversation_history.append({"role": "assistant", "content": full_response})
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]


def create_chat_engine(api_key: Optional[str] = None) -> ChatEngine:
    return ChatEngine(ClaudeClient(api_key))
