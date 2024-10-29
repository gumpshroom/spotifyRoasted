from django.shortcuts import render
from django.http import HttpResponse
from groq import Groq
import json

with open('auth.json') as f:
    GROQ_KEY = json.load(f)['groq']
client = Groq(
    api_key=GROQ_KEY,
)

def home(request):
    return render(request, 'web/home.html')
def generateDescription(request):
    if request.method == 'GET' and request.GET.get('songNameArtist') and request.GET.get('songType'):

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Make a passive-aggressive 2-3 sentence roast using sarcasm about liking the song " + request.GET.get('songNameArtist') + ", a " + request.GET.get('songType') + " track. Do not prefix with anything, only output the response."
                }
            ],
            model="llama3-8b-8192",
        )
        return HttpResponse(chat_completion.choices[0].message.content)
    else:
        return HttpResponse("")
