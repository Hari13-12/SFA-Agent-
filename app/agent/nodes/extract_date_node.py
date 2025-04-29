from ..core.state_models import State
from datetime import datetime, timedelta
from ..core.llm_manager import LLMManger


def extract_date_from_query(state:State):
    """
    Uses Gemini LLM to parse dates from natural language queries.
    Returns date in 'YYYY-MM-DD' format or None if parsing fails.
    """

    llm = LLMManger()

    
    user_query = state["messages"][-1].content
    today = datetime.today()
    today_str = today.strftime("%Y-%m-%d")
    today_weekday = today.strftime("%A")
    current_year = today.year 
    
    prompt = f"""
Today is {today_str} ({today_weekday}) and current year is {current_year}.

Your task is to:
1. Analyze the user's query strictly for date-related content
2. If a specific date or relative date is mentioned, convert it to ISO format (YYYY-MM-DD)
3. If no date is detected or the query is unrelated to dates, return today's date in ISO format

Date detection patterns to recognize:
- Absolute dates (e.g., "March 19, 2025", "2024-12-25")
- Relative dates (e.g., "next Monday", "2 weeks ago", "in 3 days")
- Implied dates (e.g., "due tomorrow", "deadline next week")
- Weekday references (e.g., "last Friday", "this coming Wednesday")

Examples:
- "What's due on March 19, 2025?" → 2025-03-19
- "Schedule meeting next Monday" → {today + timedelta(days=(7 - today.weekday()) % 7):%Y-%m-%d}
- "When was last Friday?" → {today - timedelta(days=(today.weekday() - 4) % 7):%Y-%m-%d}
- "2024-12-25" → 2024-12-25
- "Remind me in 3 days" → {today + timedelta(days=3):%Y-%m-%d}
- "Reports from 2 weeks ago" → {today - timedelta(weeks=2):%Y-%m-%d}
- "Hello" → {today_str}
- "How are you?" → {today_str}
- "What's the weather forecast?" → {today_str}
- "Tell me a joke" → {today_str}

Respond ONLY with the ISO date, no explanations or additional text.
Parse and return date for this query: "{user_query}"
    """
    
    try:
        response = llm.invoke(prompt)
        state["date"] = response.content.strip()
        return state

    except Exception as e:
        print(f"Error parsing date: {str(e)}")
    
    state["date"] = today_str
    return state

