from django.contrib.auth.forms import AuthenticationForm, authenticate
from django.contrib.auth import logout, authenticate, login, get_user
from idle_app.forms import RegistrationForm
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, Http404
from idle_app import game_api as api
from idle_app.models import UserGame, Game, PlayerItem, Item
import json
import datetime

# from django.contrib.auth.decorators import login_required
# from django.contrib.auth import login, authenticate
# from django.contrib.auth.forms import UserCreationForm
# from django.shortcuts import render, redirect

def landing(request):
    """
    api.create_game(request) Returns a UserGame
    object for implementing the create game button
    """
    print(api.create_game(request))
    if request.user.is_authenticated:
        last_game = None
        try:
            last_game = UserGame.objects.filter(user=get_user(request)).reverse()[0].game
        except Exception:
            pass
        return render(request, 'landing.html', {
            "default_linking_code":  "sb34b34jhb35hbk35"})
    else:
        return HttpResponseRedirect('/idle_app/login')


def login_view(request):
    if request.user.is_authenticated:
        return render(request, 'landing.html', )

    if request.method == 'GET':
        form = AuthenticationForm()
        return render(request, '_login.html', {'form': form})

    if request.method == 'POST':
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                print(user, request)
                login(request, user)
                return HttpResponseRedirect('/idle_app/landing/')
            else:
                print('User not found')
                return render(request, '_login.html', {'form': form})
        else:
            # If there were errors, we render the form with these
            # errors
            return render(request, '_login.html', {'form': form})


def logout_view(request):
    logout(request)
    return render(request, '_logout.html')


def game(request, linkingCode):
    current_user = get_user(request)
    print("the user id=%d"%current_user.id)
    if current_user.is_anonymous:
        return HttpResponseRedirect('/idle_app/login/')
    try:
        the_game = Game.objects.get(linkingCode=linkingCode)
        print("found game")
        try:
            userGame = UserGame.objects.get(game=the_game, user=current_user)
        except Exception:
            print("did not find user in this game yet")
            userGame = UserGame(
                            user=current_user,
                            game=the_game,
                            wealth=0,
                        )
            userGame.save()
    except Exception:
        userGame = api.create_game(request)
        the_game = userGame.game
    me,partner,partners_stuff = None,None,None
    try: #  and see if we have a partner yet
        partner = UserGame.objects.filter(game=the_game).exclude(user=current_user)
        partners_stuff = PlayerItem.objects.filter({'game':the_game,'user':partner.user})
        me = UserGame.objects.filter(game=the_game).exclude(user=partner.user)
    except Exception:
        me = UserGame.objects.filter(game=the_game)

    my_stuff = PlayerItem.objects.filter(game=the_game).filter(user=current_user)
    possible_items = list(Item.objects.all())

    game_data = {
        "game": the_game,
        "me": me,
        "my_stuff": my_stuff,
        "partner": partner,
        "partners_stuff": partners_stuff,
        "possible_items": possible_items,
    }
    saved_game_state = {
        "perks": ["snowflake", '', ''],
        "coins": {"username": 10,
                  "username2": 122},
        "items": {"username": ['calculator', 'mobile', 'desktop'],
                  "username2": ['calculator']},
        "tips": ["A hot tip for my Bitcoin Bro!",
                 "Another tip...."],
        "elapsed_time": 100,
        "linking_code": the_game.linkingCode
    }
    return render(request, 'game.html',
                  {"game_data": saved_game_state,
                    "saved_game": game_data
                   }
                  )


def posttest(request):
    print('Post received.')
    if request.method == 'POST':
        data=json.loads(request.POST.get("data", "0"))
        print(data)
        for i in data:
            print(i, data[i])
        return HttpResponse(json.dumps('test_response_info'), content_type='application/json')


def signup(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            new_user = authenticate(username=form.cleaned_data['username'],
                                    password=form.cleaned_data['password1'],
                                    )
            login(request, new_user)
            return HttpResponseRedirect('/idle_app/landing/')
    else:
        form = RegistrationForm()
    return render(request, 'sign_up.html', {'form': form})


def my_games(request):
    # display the details of each of the games belonging to the user

    current_user = get_user(request)
    # if user isn't logged in, redirect to login page
    if current_user.is_anonymous:
        return HttpResponseRedirect('/idle_app/login/')

    game_objects = UserGame.objects.filter(user=current_user)
    game_instances = []

    # for each game_objects, build a game_instance, and add it to game_instances
    for i in range(0, len(game_objects)):

        linking_code = game_objects[i].game.linkingCode
        date_created_object = game_objects[i].game.creationDate
        date_created = str(date_created_object)

        # get partner's name for the game_instance, or set other_user to "none" if no current partner
        partners_game_objects = UserGame.objects.filter(game=game_objects[i].game).exclude(user=current_user)
        if len(partners_game_objects) > 0:
            other_user = str(partners_game_objects[i].user)
        else:
            other_user = "None"

        wealth = str(game_objects[i].wealth)
        time_played = str(game_objects[i].timePlayed)

        game_instance = {
            "linking_code": linking_code,
            "date_created": date_created,
            "other_user": other_user,
            "wealth": wealth,
            "time_played": time_played,
            "pk": game_objects[i].pk,
        }

        game_instances.append(game_instance)

    # return the page with game_instances
    return render(request, 'my_games.html', {
        "game_instances": game_instances,
    }
                  )


def delete_game(request, argument_linking_code):
    current_user = get_user(request)
    if current_user.is_anonymous:
        return HttpResponseRedirect('/idle_app/login/')

    # if it is an ajax request
    if request.is_ajax():
        # try to get Game object where player = current_user
        game_object = Game.objects.filter(player=current_user).filter(linkingCode=argument_linking_code)
        # if there is no such object, delete Game object where partner = current_user
        if len(game_object) == 0:
            game_object = Game.objects.filter(partner=current_user).filter(linkingCode=argument_linking_code)
        # delete the associated UserGame objects and the Game object
        UserGame.objects.filter(game=game_object[0]).delete()
        game_object.delete()

        return HttpResponse()
    else:
        raise Http404