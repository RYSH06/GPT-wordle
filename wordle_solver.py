from google import genai
import os
from dotenv import load_dotenv
import threading
from wordle_scraper import scrape_wordle_status

load_dotenv()
API_KEY = os.getenv('API_KEY')

client = genai.Client(api_key=API_KEY)

chat = client.chats.create(model="gemini-3-flash-preview")

counter = 0
message = "I am attempting today's wordle. Give me a 5 letter word to start. Put the word between underbars (_)."

while counter < 6:
    print(message)
    res = chat.send_message(message).text
    print(res)
    message = scrape_wordle_status(res[res.index("_") + 1:res.index("_") + 6], counter + 1) + "What word should I try next?"
