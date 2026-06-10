from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit, FileManagementToolkit
from dotenv import load_dotenv
import os
import requests
from langchain_core.tools import Tool
from langchain_community.tools import WikipediaQueryRun
from langchain_experimental.tools import PythonAstREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities import WikipediaAPIWrapper


load_dotenv(override=True)
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
serper = GoogleSerperAPIWrapper()
wikipedia = WikipediaAPIWrapper()

async def playwright_tools():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


def push_notification(text: str):
    """Send a push notification to the user."""
    requests.post(pushover_url, data={
        "token": pushover_token,
        "user": pushover_user,
        "message": text,
    })
    return "success"


def get_file_tools():
    toolkit = FileManagementToolkit()
    return toolkit.get_tools()


def other_tools():
    push_tool = Tool(name="send_push_notification", func=push_notification, description="Use this tool when you want to send a push notification to the user." )
    file_tools = get_file_tools()
    
    tool_search = Tool(name="search", func=serper.run, description="Use this tool to search the web for up-to-date information.")
    
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)
    
    python_repl = PythonAstREPLTool()
    
    return [push_tool, tool_search, wiki_tool, python_repl] + file_tools
