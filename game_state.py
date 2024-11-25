from enum import Enum
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import random

class Role(Enum):
    LIBERAL = "liberal"
    FASCIST = "fascist"
    HITLER = "hitler"

class PolicyCard(Enum):
    LIBERAL = "liberal"
    FASCIST = "fascist"

class GamePhase(Enum):
    NOMINATING_CHANCELLOR = "nominating_chancellor"
    VOTING = "voting"
    PRESIDENT_DISCARD = "president_discard"
    CHANCELLOR_DISCARD = "chancellor_discard"
    POWER_ACTION = "power_action"
    GAME_OVER = "game_over"

class GameEventType(Enum):
    CHANCELLOR_NOMINATION = "chancellor_nomination"
    VOTE = "vote_cast"
    ELECTION_RESULT = "election_result"
    POLICY_ENACTED = "policy_enacted"
    POWER_ACTION = "power_action"
    DISCUSSION = "discussion"
    GAME_START = "game_start"
    GAME_END = "game_end"

@dataclass
class Player:
    id: str
    name: str
    role: Role
    is_alive: bool = True

@dataclass
class GameEvent:
    event_type: GameEventType
    timestamp: datetime
    actor_id: str
    action_details: Dict[str, Any]
    justification: Optional[str] = None
    discussion: List[Dict[str, str]] = None

    def __post_init__(self):
        if self.discussion is None:
            self.discussion = []

@dataclass
class PrivateInfo:
    recipient_id: str
    info_type: str
    content: Any
    expiry_turn: int

@dataclass
class PendingVote:
    player_id: str
    vote: bool
    justification: str
    timestamp: datetime

class SecretHitler:
    def __init__(self, player_ids: List[str], player_names: List[str]):
        if len(player_ids) < 5 or len(player_ids) > 10:
            raise ValueError("Game requires 5-10 players")
        
        # Core game state
        self.players = {
            "system": Player(id="system", name="System", role=Role.LIBERAL)  # Role doesn't matter for system
        }
        # Add regular players
        self.players.update(self._setup_players(player_ids, player_names))
        
        self.policy_deck: List[PolicyCard] = []
        self.discard_pile: List[PolicyCard] = []
        self.liberal_policies = 0
        self.fascist_policies = 0
        self.president_index = 0
        self.chancellor_id: Optional[str] = None
        self.last_government: Tuple[str, str] = (None, None)
        self.phase = GamePhase.NOMINATING_CHANCELLOR
        self.votes: Dict[str, bool] = {}
        self.pending_votes: Dict[str, PendingVote] = {}
        
        self.current_policies: List[PolicyCard] = []
        
        # Logging and discussion state
        self.game_events: List[GameEvent] = []
        self.private_info: Dict[str, List[PrivateInfo]] = {pid: [] for pid in player_ids}
        self.current_turn = 0
        self.discussion_limit = 5
        
        # Initialize the game
        self._initialize_deck()
        self._log_event(
            GameEventType.GAME_START,
            "system",
            {"player_count": len(player_ids)},
            "Game initialized"
        )

    def _setup_players(self, player_ids: List[str], player_names: List[str]) -> Dict[str, Player]:
        num_players = len(player_ids)
        roles = {
            5: [Role.HITLER] + [Role.FASCIST] + [Role.LIBERAL] * 3,
            6: [Role.HITLER] + [Role.FASCIST] + [Role.LIBERAL] * 4,
            7: [Role.HITLER] + [Role.FASCIST] * 2 + [Role.LIBERAL] * 4,
            8: [Role.HITLER] + [Role.FASCIST] * 2 + [Role.LIBERAL] * 5,
            9: [Role.HITLER] + [Role.FASCIST] * 3 + [Role.LIBERAL] * 5,
            10: [Role.HITLER] + [Role.FASCIST] * 3 + [Role.LIBERAL] * 6
        }[num_players]
        
        random.shuffle(roles)
        return {
            player_id: Player(id=player_id, name=name, role=role)
            for player_id, name, role in zip(player_ids, player_names, roles)
        }

    def _initialize_deck(self):
        self.policy_deck = [PolicyCard.LIBERAL] * 6 + [PolicyCard.FASCIST] * 11
        random.shuffle(self.policy_deck)

    def _draw_policies(self, count: int = 3) -> List[PolicyCard]:
        if len(self.policy_deck) < count:
            self.policy_deck.extend(self.discard_pile)
            self.discard_pile = []
            random.shuffle(self.policy_deck)
        return [self.policy_deck.pop() for _ in range(count)]

    def _log_event(self, 
                   event_type: GameEventType, 
                   actor_id: str, 
                   action_details: Dict[str, Any], 
                   justification: Optional[str] = None) -> GameEvent:
        event = GameEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            actor_id=actor_id,
            action_details=action_details,
            justification=justification
        )
        self.game_events.append(event)
        return event

    def add_discussion_message(self, 
                             event_index: int, 
                             player_id: str, 
                             message: str) -> bool:
        if 0 <= event_index < len(self.game_events):
            event = self.game_events[event_index]
            if len(event.discussion) < self.discussion_limit:
                event.discussion.append({
                    "player_id": player_id,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                })
                return True
        return False

    def add_private_info(self, 
                        recipient_id: str, 
                        info_type: str, 
                        content: Any, 
                        duration_turns: int = 1):
        expiry_turn = self.current_turn + duration_turns
        info = PrivateInfo(recipient_id, info_type, content, expiry_turn)
        self.private_info[recipient_id].append(info)

    def get_visible_events(self, player_id: str) -> List[Dict]:
        return [
            {
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "actor": self.players[event.actor_id].name,
                "details": event.action_details,
                "justification": event.justification,
                "discussion": event.discussion
            }
            for event in self.game_events
        ]

    def get_private_info(self, player_id: str) -> List[Dict]:
        return [
            {
                "type": info.info_type,
                "content": info.content
            }
            for info in self.private_info[player_id]
            if info.expiry_turn >= self.current_turn
        ]
        
    def get_active_players(self) -> Dict[str, Player]:
        """Returns dictionary of active players (alive and not system)."""
        return {
            pid: player 
            for pid, player in self.players.items() 
            if player.is_alive and pid != "system"
        }

    def get_human_players(self) -> Dict[str, Player]:
        """Returns dictionary of all non-system players."""
        return {
            pid: player
            for pid, player in self.players.items()
            if pid != "system"
        }

    def get_president_id(self) -> str:
        """Gets the current president's ID."""
        active_players = list(self.get_active_players().keys())
        return active_players[self.president_index % len(active_players)]

    def get_game_state(self, player_id: Optional[str] = None):
        state = {
            "phase": self.phase.value,
            "liberal_policies": self.liberal_policies,
            "fascist_policies": self.fascist_policies,
            "president_id": self.get_president_id(),
            "chancellor_id": self.chancellor_id,
            "last_government": self.last_government,
            "players": {
                pid: {
                    "name": p.name,
                    "is_alive": p.is_alive,
                } for pid, p in self.get_human_players().items()
            },
            "deck_size": len(self.policy_deck),
            "discard_size": len(self.discard_pile)
        }
        
        if player_id:
            player_role = self.players[player_id].role
            state.update({
                "your_role": player_role.value,
                "events": self.get_visible_events(player_id),
                "private_info": self.get_private_info(player_id)
            })
            
            if player_role in [Role.FASCIST, Role.HITLER]:
                state["fascists"] = [
                    pid for pid, p in self.get_human_players().items()
                    if p.role in [Role.FASCIST, Role.HITLER]
                ]
        
        return state

    def nominate_chancellor(self, president_id: str, chancellor_id: str, justification: str) -> bool:
        if (self.phase != GamePhase.NOMINATING_CHANCELLOR or
            chancellor_id == self.get_president_id() or
            chancellor_id in self.last_government):
            return False
            
        self.chancellor_id = chancellor_id
        self.phase = GamePhase.VOTING
        self.votes = {}
        
        self._log_event(
            GameEventType.CHANCELLOR_NOMINATION,
            president_id,
            {"nominee": chancellor_id},
            justification
        )
        return True

    def vote(self, player_id: str, vote: bool, justification: str) -> Optional[bool]:
        """
        Handle a player's vote, storing it until all votes are in.
        Returns: None if more votes needed, True/False when voting complete
        """
        if self.phase != GamePhase.VOTING or not self.players[player_id].is_alive:
            return None
            
        # Store the vote in pending_votes instead of logging immediately
        self.pending_votes[player_id] = PendingVote(
            player_id=player_id,
            vote=vote,
            justification=justification,
            timestamp=datetime.now()
        )
        
        self.votes[player_id] = vote
        
        if len(self.votes) == len(self.get_active_players()):
            passed = sum(self.votes.values()) > len(self.votes) / 2
            
            # Log all individual votes in chronological order
            sorted_votes = sorted(
                self.pending_votes.values(),
                key=lambda x: x.timestamp
            )
            
            for pending_vote in sorted_votes:
                self._log_event(
                    GameEventType.VOTE,
                    pending_vote.player_id,
                    {"vote": pending_vote.vote},
                    pending_vote.justification
                )
            
            # Clear pending votes
            self.pending_votes.clear()
            
            # Log election result
            supporters = [pid for pid, v in self.votes.items() if v]
            opposers = [pid for pid, v in self.votes.items() if not v]
            
            self._log_event(
                GameEventType.ELECTION_RESULT,
                "system",
                {
                    "result": "passed" if passed else "failed",
                    "president_id": self.get_president_id(),
                    "chancellor_id": self.chancellor_id
                },
                f"Votes: {sum(self.votes.values())}/{len(self.votes)}, "
                f"Supported by {[self._get_player_name(p) for p in supporters]}, "
                f"Opposed by {[self._get_player_name(p) for p in opposers]}"
            )
            
            if passed:
                self.last_government = (self.get_president_id(), self.chancellor_id)
                self.current_policies = self._draw_policies()
                self.phase = GamePhase.PRESIDENT_DISCARD
            else:
                self._advance_president()
                self.phase = GamePhase.NOMINATING_CHANCELLOR
            return passed
            
        return None

    def president_discard(self, index: int) -> bool:
        if self.phase != GamePhase.PRESIDENT_DISCARD or not 0 <= index < len(self.current_policies):
            return False
            
        self.discard_pile.append(self.current_policies.pop(index))
        self.phase = GamePhase.CHANCELLOR_DISCARD
        return True

    def chancellor_discard(self, index: int) -> Optional[str]:
        if self.phase != GamePhase.CHANCELLOR_DISCARD or not 0 <= index < len(self.current_policies):
            return None
            
        self.discard_pile.append(self.current_policies.pop(index))
        enacted_policy = self.current_policies.pop()
        
        if enacted_policy == PolicyCard.LIBERAL:
            self.liberal_policies += 1
        else:
            self.fascist_policies += 1
            
        self._log_event(
            GameEventType.POLICY_ENACTED,
            self.chancellor_id,
            {"policy": enacted_policy.value},
            None
        )
            
        # Check win conditions
        if self.liberal_policies >= 5:
            self.phase = GamePhase.GAME_OVER
            return "LIBERALS_WIN"
        elif self.fascist_policies >= 6:
            self.phase = GamePhase.GAME_OVER
            return "FASCISTS_WIN"
            
        if self._requires_power_action():
            self.phase = GamePhase.POWER_ACTION
        else:
            self._advance_president()
            self.phase = GamePhase.NOMINATING_CHANCELLOR
            
        return enacted_policy.value

    def president_peek_policies(self, president_id: str):
        if len(self.policy_deck) >= 3:
            next_policies = self.policy_deck[-3:]
            self.add_private_info(
                president_id,
                "policy_peek",
                {"upcoming_policies": [p.value for p in next_policies]},
                duration_turns=1
            )

    def execute_power_action(self, action: str, target_id: Optional[str] = None) -> bool:
        if self.phase != GamePhase.POWER_ACTION:
            return False
            
        self._log_event(
            GameEventType.POWER_ACTION,
            self.get_president_id(),
            {"action": action, "target": target_id},
            None
        )
        
        self._advance_president()
        self.phase = GamePhase.NOMINATING_CHANCELLOR
        return True

    def _advance_president(self):
        alive_players = [pid for pid, p in self.players.items() if p.is_alive]
        self.president_index = (self.president_index + 1) % len(alive_players)
        self.current_turn += 1
        
        # Clean up expired private information
        for player_id in self.private_info:
            self.private_info[player_id] = [
                info for info in self.private_info[player_id]
                if info.expiry_turn >= self.current_turn
            ]
            
    def _get_player_name(self, player_id: str) -> str:
        return self.players[player_id].name

    def _requires_power_action(self) -> bool:
        # Implement based on fascist track position
        return False