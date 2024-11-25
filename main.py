import sys
from game_manager import GameManager 

if __name__ == "__main__":
    player_ids = ["p1", "p2", "p3", "p4", "p5"]
    player_names = ["Alice", "Bob", "Charlie", "David", "Eve"]
    player_types = {pid: "human" for pid in player_ids}
    
    game = GameManager(player_ids, player_names, player_types,
                       discussion_limit=0)
    game.play_game()