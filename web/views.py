
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from groq import Groq
from web.models import User
from datetime import datetime
from dotenv import load_dotenv
import os
import json
import requests
import base64
import hashlib
from django.http import JsonResponse


load_dotenv()
APP_URL = os.getenv('APP_URL')

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
                    print('this my user!!!')
                    print(user.access_token)
                    print(user.wraps)
                    print(user.spotify_id)
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
        now = datetime.now()

        # Format the date and time
        formatted_date = now.strftime("%B {}, %Y at {}").format(now.day, now.strftime("%I:%M %p"))

        # Remove leading zero for day if it exists
        if now.day < 10:
            formatted_date = formatted_date.replace(f" {now.day}", f" {now.day}")


        # get user
        try:
            user = User.objects.get(access_token=request.GET.get('accessToken'))
            id = user.spotify_id + len(user.wraps).__str__()
            wrap = {
                'name': "Wrap from " + formatted_date,
                'topSongRoast': "",
                'topGenreRoast': "",
                'topArtistRoast': "",
                'topAlbumRoast': "",
                'summaryRoast': "",
                'topSongImage': "",
                'id': hashlib.md5(id.encode()).hexdigest(),
                'uid': user.spotify_id
            }

            topSong, topArtist, topGenre, topAlbum = None, None, None, None
            url = 'https://api.spotify.com/v1/me/top/tracks'
            res = requests.get(url, headers={'Authorization': 'Bearer ' + user.access_token})
            if res.status_code == 200:
                topAlbum = res.json()['items'][0]['album']['name']
            else:
                return HttpResponse("spotify api failed 0")
            url = 'https://api.spotify.com/v1/me/top/tracks'
            res = requests.get(url, headers={'Authorization': 'Bearer ' + user.access_token})
            if res.status_code == 200:
                topSong = res.json()['items'][0]['name']
                wrap['topSongImage'] = res.json()['items'][0]['album']['images'][0]['url']
            else:
                return HttpResponse("spotify api failed 1")
            url = 'https://api.spotify.com/v1/me/top/artists'
            res = requests.get(url, headers={'Authorization': 'Bearer ' + user.access_token})
            if res.status_code == 200:
                topArtist = res.json()['items'][0]['name']
            else:
                return HttpResponse("spotify api failed2")
            url = 'https://api.spotify.com/v1/me/top/artists'
            res = requests.get(url, headers={'Authorization': 'Bearer ' + user.access_token})
            if res.status_code == 200:
                topGenre = res.json()['items'][0]['genres'][0]
            else:
                return HttpResponse("spotify api failed 5")
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": "Make a creative 2-3 sentence roast parody of a Spotify Wrapped about the user liking the song " + topSong + ", a " +
                                   topGenre + " track. Make sure to mention the top song, and use dry humanlike humor. Don't start with 'wow'. Do not use big ai-sounding words. Do not prefix with anything, only output the response. Don't start with 'here's a parody...'. Roast me, the user."
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
                                   topGenre + " music artist. Make sure to mention the top artist, and use creative, witty humanlike humor. Do not use big ai-sounding words. Do not prefix with anything, only output the response. Do not use statistics. Don't start with 'here's a parody...'. Roast me, the user."
                    }
                ],
                model="llama3-8b-8192",
            )
            wrap['topArtistRoast'] = chat_completion.choices[0].message.content
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": "Make a witty 2-3 sentence roast parody of a Spotify Wrapped about me liking " + topGenre + " music. Make sure to mention the top genre, and use dry, creative but not overly sarcastic humanlike humor. Don't start with 'wow'. Do not use big ai-sounding words. Do not prefix with anything, only output the response. Do not use statistics. Don't start with 'here's a parody...'. Roast me, the user."
                    }
                ],
                model="llama3-8b-8192",
            )
            wrap['topGenreRoast'] = chat_completion.choices[0].message.content
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": "Make a passive-aggressive 2-3 sentence roast about me liking the albums " + topAlbum + " and other" + topGenre + "music. Specify the album you are roasting. Use subtle, dry, sarcastic, humanlike humor. Don't start with 'wow'. Do not use big ai-sounding words. Do not prefix with anything, only output the response. Do not use statistics. Don't start with 'here's a parody...'. Roast me, the user."
                    }
                ],
                model="llama3-8b-8192",
            )
            wrap['topAlbumRoast'] = chat_completion.choices[0].message.content
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": "Make a passive-aggressive 2-3 sentence roast parody of a Spotify Wrapped summary slide. I like " + topArtist + " and other " + topGenre + " music. Use subtle, dry, sarcastic, humanlike humor. Don't start with 'wow'. Do not use big ai-sounding words. Do not prefix with anything, only output the response. Do not use statistics. Don't start with 'here's a parody...'. Roast me, the user."
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
                str = str[:-2] + "], \"wrapIds\": ["
                for i in range(len(user.wraps)):
                    str += '"' + user.wraps[i.__str__()]['id'] + '", '
                str = str[:-2] + "] , \"uid\": \"" + user.spotify_id + "\"}"

                return HttpResponse(json.dumps(str))
            else:
                return HttpResponse('{ "error": "you have no wraps" }')
        except User.DoesNotExist:
            return HttpResponse("user not found")
    else:
        return redirect('/')
def permalink(request):
    if request.method == 'GET' and request.GET.get('id') and request.GET.get('uid'):
        try:
            user = User.objects.get(spotify_id=request.GET.get('uid'))
            if user.wraps is not None:
                for i in range(len(user.wraps)):
                    if user.wraps[i.__str__()]['id'] == request.GET.get('id'):
                        wrap = user.wraps[i.__str__()]
                        return render(request, 'web/wrap.html', {'wrap': wrap})
            else:
                return HttpResponse('{ "error": "wrap not found" }')
        except User.DoesNotExist:
            return HttpResponse("wrap not found")
    return HttpResponse("400 Bad Request")
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


def contact(request):
    developers = [
        {"name": "Aaron Luu", "email": "aluu31@gatech.edu", "image": "images/AaronLuu.PNG"},
        {"name": "Patrick Del Rio", "email": "prio3@gatech.edu", "image": "images/PatrickDelRio.PNG"},
        {"name": "Nathan Nguyen", "email": "nnguyen402@gatech.edu", "image": "images/NathanNguyen.PNG"},
        {"name": "Eric Yang", "email": "eyang317@gatech.edu", "image": "images/EricYang.PNG"},
        {"name": "Bao Nguyen", "email": "bnguyen324@gatech.edu", "image": "images/BaoNguyen.PNG"}
    ]
    return render(request, "web/contact.html", {'developers': developers})


def deleteWrap(request):
    if request.method == 'DELETE' and request.GET.get('accessToken') and request.GET.get('wrapId'):
        try:
            user = User.objects.get(access_token=request.GET.get('accessToken'))
            wrap_id = request.GET.get('wrapId')

            # Ensure the wraps dictionary is not empty
            if user.wraps:
                wraps = user.wraps

                # Check if the wrap ID exists
                if wrap_id in wraps:
                    # Remove the wrap
                    del wraps[wrap_id]

                    # Reindex the wraps (convert keys to strings and reorder numerically)
                    wraps = {str(i): wrap for i, wrap in enumerate(wraps.values())}
                    user.wraps = wraps
                    user.save()

                    return JsonResponse({"message": "Wrap deleted successfully."}, status=200)
                else:
                    return JsonResponse({"error": "Wrap ID not found."}, status=404)
            else:
                return JsonResponse({"error": "No wraps to delete."}, status=404)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found."}, status=404)
    else:
        return JsonResponse({"error": "Invalid request."}, status=400)


def your_view(request):
    return render(request, 'web/wrap.html', {})