from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import Runnable
from app.core.config import Settings

Appsettings = Settings()


class LLMManger:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="models/gemini-1.5-flash",
           
            temperature=1,
           
            api_key=Appsettings.GEMINI_API_KEY
        )
 
    def get_llm(self):
        return self.llm

    def invoke(self,message):
        return self.llm.invoke(message)