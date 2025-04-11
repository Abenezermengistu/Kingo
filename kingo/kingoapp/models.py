from django.db import models
from django.contrib.auth.models import AbstractUser

class UserCustom(AbstractUser):
    phone = models.CharField(max_length=15, unique=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Default balance
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.username} ({self.first_name} {self.last_name})"

class BingoBoard(models.Model):
    board_number = models.IntegerField(unique=True)
    is_active = models.BooleanField(default=True)  # If board is currently being played

    def __str__(self):
        return f"Board {self.board_number}"

import uuid

class Player(models.Model):
    user_identifier = models.CharField(
        max_length=255,
        default=uuid.uuid4,  # Automatically generate a UUID for new records
        unique=False  # Keep as False unless you're sure it should be unique globally
    )
    board = models.ForeignKey(BingoBoard, on_delete=models.CASCADE, related_name="players")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_identifier', 'board')

class GameSession(models.Model):
    board = models.OneToOneField(BingoBoard, on_delete=models.CASCADE)
    called_numbers = models.JSONField(default=list)  # Stores called numbers
    bet_amount = models.IntegerField(default=10)
    is_finished = models.BooleanField(default=False)

    def __str__(self):
        return f"Game on Board {self.board.board_number}"
