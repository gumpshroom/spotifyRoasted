from django.shortcuts import render, redirect
from django.http import HttpResponse
from groq import Groq
from web.models import User
from datetime import datetime
import json
import requests
import base64

APP_URL = 'http://localhost:8000'

data = json.load(open('auth.json'))
GROQ_KEY = data['groq']
SPOTIFY_CLIENT_ID = data['spotifyId']
SPOTIFY_CLIENT_SECRET = data['spotifySecret']
client = Groq(
    api_key=GROQ_KEY,
)

def home(request):
    return render(request, 'web/home.html')

def oauth(request):
    if request.method == 'GET':
        url = 'https://accounts.spotify.com/authorize?'
        data = {
            'response_type': 'code',
            'client_id': SPOTIFY_CLIENT_ID,
            'redirect_uri': APP_URL + '/oauthCallback',
            'scope': 'user-library-read user-top-read'
        }
        return redirect(url + '&'.join([key + '=' + value for key, value in data.items()]))
    else:
        return HttpResponse("400 Bad Request")

def oauthCallback(request):
    if request.method == 'GET' and request.GET.get('code'):
        url = 'https://accounts.spotify.com/api/token'
        data = {
            'grant_type': 'authorization_code',
            'code': request.GET.get('code'),
            'redirect_uri': APP_URL + '/oauthCallback',
            'client_id': SPOTIFY_CLIENT_ID,
            'client_secret': SPOTIFY_CLIENT_SECRET
        }
        response = requests.post(url, data=data, headers= {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + base64.b64encode((SPOTIFY_CLIENT_ID + ':' + SPOTIFY_CLIENT_SECRET).encode('ascii')).decode('ascii')
        })
        if response.status_code == 200:
            url = 'https://api.spotify.com/v1/me'
            res = requests.get(url, headers={'Authorization': 'Bearer ' + response.json()['access_token']})

            if res.status_code == 200:
                try:
                    user = User.objects.get(spotify_id=res.json()['id'])
                    user.access_token = response.json()['access_token']
                    user.save()
                    return render(request, 'web/roasted.html', {'accessToken': response.json()['access_token'], 'welcomeBack': 'true'})
                except User.DoesNotExist:
                    user = User(spotify_id=res.json()['id'], access_token=response.json()['access_token'])
                    user.save()
                    return render(request, 'web/roasted.html', {'accessToken': response.json()['access_token'], 'welcomeBack': 'false'})
            else:
                return HttpResponse("spotify api failed")
        return HttpResponse("oauth failed")

def generateWrap(request):
    if request.method == 'GET' and request.GET.get('accessToken'):
        # get user
        try:
            user = User.objects.get(access_token=request.GET.get('accessToken'))
            wrap = {
                'name': "Wrap from " + datetime.now().strftime("%B %-d, %Y at %-I:%M %p"),
                'topSongRoast': "",
                'topGenreRoast': "",
                'topArtistRoast': "",
                'summaryRoast': ""
            }
            url = 'https://api.spotify.com/v1/me/top/tracks'
            res = requests.get(url, headers={'Authorization': 'Bearer ' + user.access_token})
            topSong, topArtist, topGenre = None, None, None
            if res.status_code == 200:
                topSong = res.json()['items'][0]['name']
            else:
                return HttpResponse("spotify api failed")
            url = 'https://api.spotify.com/v1/me/top/artists'
            res = requests.get(url, headers={'Authorization': 'Bearer ' + user.access_token})
            if res.status_code == 200:
                topArtist = res.json()['items'][0]['name']
            else:
                return HttpResponse("spotify api failed")
            url = 'https://api.spotify.com/v1/me/top/artists'
            res = requests.get(url, headers={'Authorization': 'Bearer ' + user.access_token})
            if res.status_code == 200:
                topGenre = res.json()['items'][0]['genres'][0]
            else:
                return HttpResponse("spotify api failed")
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": "Make a passive-aggressive 2-3 sentence roast parody of a Spotify Wrapped about me liking the song " + topSong + ", a " +
                                   topGenre + " track. Use subtle, dry, sarcastic humor, humanlike humor. Do not use big ai-sounding words. Do not prefix with anything, only output the response."
                    }
                ],
                model="llama3-8b-8192",
            )
            wrap['topSongRoast'] = chat_completion.choices[0].message.content
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": "Make a passive-aggressive 2-3 sentence roast parody of a Spotify Wrapped about me liking the artist " + topArtist + ", a " +
                                   topGenre + " music artist. Use subtle, dry, sarcastic humanlike humor. Do not use big ai-sounding words. Do not prefix with anything, only output the response. Do not use quotes. Do not use statistics."
                    }
                ],
                model="llama3-8b-8192",
            )
            wrap['topArtistRoast'] = chat_completion.choices[0].message.content
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": "Make a passive-aggressive 2-3 sentence roast parody of a Spotify Wrapped about me liking " + topGenre + " music. Use subtle, dry, sarcastic, humanlike humor. Do not use big ai-sounding words. Do not prefix with anything, only output the response. Do not use statistics."
                    }
                ],
                model="llama3-8b-8192",
            )
            wrap['topGenreRoast'] = chat_completion.choices[0].message.content
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": "Make a passive-aggressive 2-3 sentence roast parody of a Spotify Wrapped about my music taste summarizing the Wrapped. I like " + topArtist + " and other " + topGenre + " music. Use subtle, dry, sarcastic, humanlike humor. Do not use big ai-sounding words. Do not prefix with anything, only output the response. Do not use statistics."
                    }
                ],
                model="llama3-8b-8192",
            )
            wrap['summaryRoast'] = chat_completion.choices[0].message.content
            wraps = user.wraps | {}
            wraps[len(wraps)] = wrap
            user.wraps = wraps
            user.save()
            return render(request, 'web/wrap.html', {'wrap': wrap})
        except User.DoesNotExist:
            return HttpResponse("user not found")

    else:
        return redirect('/')

def getWraps(request):
    if request.method == 'GET' and request.GET.get('accessToken'):
        try:
            user = User.objects.get(access_token=request.GET.get('accessToken'))
            if user.wraps is not None:
                print(user.wraps)
                str = '{ "wrapNames": ['
                for i in range(len(user.wraps)):
                    str += '"' + user.wraps[i.__str__()]['name'] + '", '
                str = str[:-2] + "] }"
                return HttpResponse(json.dumps(str))
            else:
                return HttpResponse('{ "error": "you have no wraps" }')
        except User.DoesNotExist:
            return HttpResponse("user not found")
    else:
        return redirect('/')

def getWrap(request):
    if request.method == 'GET' and request.GET.get('accessToken') and request.GET.get('wrapId'):
        try:
            user = User.objects.get(access_token=request.GET.get('accessToken'))
            if user.wraps is not None:
                wrap = user.wraps[request.GET.get('wrapId')]
                return render(request, 'web/wrap.html', {'wrap': wrap})
            else:
                return HttpResponse('{ "error": "you have no wraps" }')
        except User.DoesNotExist:
            return HttpResponse("user not found")
    else:
        return redirect('/')