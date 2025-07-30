# import os
# from dotenv import load_dotenv
# from tavily import TavilyClient

# load_dotenv()

# TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
# response = tavily_client.search("Who is Leo Messi?")


import os

svg_path = os.path.abspath("test.svg")
print(svg_path)