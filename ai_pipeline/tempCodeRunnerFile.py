import os
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

key=os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=key)

def rewrite(text):
   prompt = f"Rewrite this to be clearer and more engaging:\n{text}"
   try:
       model = genai.GenerativeModel("gemini-2.0-flash-001")
       response = model.generate_content(prompt)
       return response.text.strip()
   except Exception as e:
       print(f"rewrite failed: {e}")
       return text
def review(text):
   prompt = f"Fix grammar and improve flow:\n{text}"
   try:
       model = genai.GenerativeModel("gemini-2.0-flash-001")  
       response = model.generate_content(prompt)
       return response.text.strip()
   except Exception as e:
       print(f"review failed:{e}")
       return text

def main():
   
   if not os.path.exists("content.txt"):
       print("need content.txt first")
       return
   with open("content.txt",encoding="utf-8")as  f:
       text = f.read()
   print("rewriting...")
   better_text = rewrite(text)
   print("reviewing...")
   final_text = review(better_text)
   
   with open("rewritten.txt","w")as f:
       f.write(better_text)
   with open("reviewed.txt","w") as f:
       f.write(final_text)
   print("done -check rewritten.txt and reviewed.txt")
