from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import random
from .models import BingoBoard, GameSession, Player, UserCustom
from django.shortcuts import render
import random


def generate_bingo_card():
    def get_random_numbers(start, end, count):
        return sorted(random.sample(range(start, end + 1), count))

    card = []
    columns = {
        'B': get_random_numbers(1, 15, 5),
        'I': get_random_numbers(16, 30, 5),
        'N': get_random_numbers(31, 45, 4),
        'G': get_random_numbers(46, 60, 5),
        'O': get_random_numbers(61, 75, 5),
    }
    columns['N'].insert(2, 'FREE')

    for i in range(5):
        card.append([
            columns['B'][i],
            columns['I'][i],
            columns['N'][i],
            columns['G'][i],
            columns['O'][i]
        ])
    return card

def bingo_index(request):
    wallet = request.GET.get('wallet', 0)
    stake = request.GET.get('stake', 0)
    user_id = request.GET.get('user_id')

    board_numbers = list(range(1, 101))
    session_cards = request.session.get('bingo_cards', {})

    # Only generate if not already in session
    if not session_cards:
        session_cards = {
            str(num): generate_bingo_card() for num in board_numbers
        }
        request.session['bingo_cards'] = session_cards

    # Grab a sample card for preview (like board 1)
    sample_card = session_cards.get("1")

    context = {
        'wallet': wallet,
        'stake': stake,
        'user_id': user_id,
        'board_numbers': board_numbers,
        'bingo_cards': session_cards,
        'sample_card': sample_card
    }
    return render(request, 'index.html', context)
from django.shortcuts import render
import uuid  # Import the uuid module
from .models import BingoBoard, GameSession, Player  # Import your models

def board_view(request):
    board_number = int(request.GET.get('board'))
    wallet = request.GET.get('wallet', 0)
    stake = int(request.GET.get('stake', 10))

    user_id = request.session.get('user_id')
    if not user_id:
        user_id = str(uuid.uuid4())
        request.session['user_id'] = user_id

    board, _ = BingoBoard.objects.get_or_create(board_number=board_number)
    game_session, created = GameSession.objects.get_or_create(board=board, defaults={'bet_amount': stake})

    Player.objects.get_or_create(user_identifier=user_id, board=board)  # Use user_identifier!

    bingo_card = request.session.get(f'bingo_card_{board_number}')

    context = {
        'board': board_number,
        'wallet': wallet,
        'stake': stake,
        'user_id': user_id,  # Keep sending this for client-side logic
        'bingo_card': bingo_card,
        'game_id': game_session.id
    }
    return render(request, 'board.html', context)

# views.py
from django.http import JsonResponse

def save_selected_bingo_card(request):
    board_number = request.GET.get('board')
    all_cards = request.session.get('bingo_cards', {})
    selected_card = all_cards.get(board_number)

    if selected_card:
        request.session[f'bingo_card_{board_number}'] = selected_card
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

from django.http import JsonResponse
from .telegram_bot import get_user_wallet  # now correctly imported

def get_wallet_data(request):
    user_id = request.GET.get("user_id")
    if not user_id:
        return JsonResponse({"error": "Missing user_id"}, status=400)

    wallet = get_user_wallet(user_id)
    stake = request.GET.get("stake", 0)

    return JsonResponse({
        "wallet": wallet["balance"],
        "stake": stake
    })
