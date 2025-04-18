def check_username_exists(username):
    """Check if a username is already taken."""
    from django.contrib.auth import get_user_model
    UserCustom = get_user_model()  # Import here
    if UserCustom.objects.filter(username=username).exists():
        return False, "Username already exists. Please choose a different username."
    return True, "Username is available."

from kingoapp.models import UserCustom, Withdrawal  # replace 'your_app' with your actual app name

def get_user_by_telegram_id(telegram_id):
    try:
        return UserCustom.objects.get(telegram_user_id=str(telegram_id))  # Cast to string since it's stored as CharField
    except UserCustom.DoesNotExist:
        return None


def get_user_wallet(telegram_user_id):
    from kingoapp.models import UserCustom  # Adjust this import to your app name

    try:
        user = UserCustom.objects.get(telegram_user_id=telegram_user_id)
        return {
            'balance': float(user.balance),
            'wins': user.wins,
            'losses': user.losses,
            'deposits': getattr(user, 'deposits', 0),
            'withdrawals': float(user.withdrawals),  # Ensure withdrawals is retrieved as a float
        }
    except UserCustom.DoesNotExist:
        return {
            "balance": 0,
            "wins": 0,
            "losses": 0,
            "deposits": 0,
            "withdrawals": 0,
        }
def update_user_wallet(telegram_user_id, updates):
    try:
        user = UserCustom.objects.get(telegram_user_id=telegram_user_id)
        if 'balance' in updates:
            user.balance = updates['balance']
        if 'wins' in updates:
            user.wins = updates['wins']
        if 'losses' in updates:
            user.losses = updates['losses']
        user.save()
    except UserCustom.DoesNotExist:
        pass


def get_logged_in_user(email):
    """Retrieve logged-in user's basic information."""
    from django.contrib.auth import get_user_model
    UserCustom = get_user_model()  # Import here
    try:
        user = UserCustom.objects.get(email=email)
        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "phone": user.phone,
            "joined_at": user.joined_at.strftime("%Y-%m-%d"),
        }
    except UserCustom.DoesNotExist:
        return False, "User not found."
    except Exception as e:
        return False, f"An error occurred: {e}"

def register_user(first_name, last_name, username, email, phone, password, telegram_user_id=None, telegram_username=None):
    from django.contrib.auth import get_user_model
    UserCustom = get_user_model()

    try:
        if UserCustom.objects.filter(username=username).exists():
            return False, "Username already taken."

        user = UserCustom.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            phone=phone,
            password=password,
        )

        # Save Telegram info
        user.telegram_user_id = telegram_user_id
        user.telegram_username = telegram_username
        user.save()

        return True, "Registration complete! You can now log in."

    except Exception as e:
        return False, f"An error occurred: {e}"
