from google import genai
import os
import threading
from wordle_scraper import scrape_wordle_status


client = genai.Client(api_key="AIzaSyCkQKXWwoB_ZFfg39FpYh8N2ghkBhIKWjc")

chat = client.chats.create(model="gemini-3-flash-preview")

counter = 0
message = "I am attempting today's wordle. Give me a 5 letter word to start. Put the word between underbars (_)."

while counter < 6:
    print(message)
    res = chat.send_message(message).text
    print(res)
    scrape_wordle_status(res[res.index("_") + 1:res.index("_") + 6], counter + 1)
