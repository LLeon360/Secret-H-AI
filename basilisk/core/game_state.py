from enum import Enum
from typing import List, Dict, Optional, Tuple, Union, Any
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
class PolicyChoiceContent:
    """Content for policy selection private info"""
    role: str  # "president" or "chancellor"
    policies_seen: List[str]  # All policies that were seen
    discarded: str  # The policy that was discarded
    claimed_discard: Optional[str]  # What they claimed to discard (or None if undisclosed)
    remaining: List[str]  # Policies after discard (for president)
    enacted: Optional[str] = None  # Only for chancellor, the policy actually enacted

@dataclass
class PolicyPeekContent:
    """Content for policy peek power"""
    upcoming_policies: List[str]

@dataclass
class InvestigationContent:
    """Content for investigation power"""
    target_id: str
    party_membership: str

@dataclass
class GovernmentInfo:
    """Metadata about the government when action occurred"""
    president_id: str
    chancellor_id: str
    policy_counts: Dict[str, int]  # Current liberal/fascist counts

@dataclass
class PrivateInfo:
    recipient_id: str
    info_type: str  # "policy_choice", "policy_peek", "investigation"
    content: Union[PolicyChoiceContent, PolicyPeekContent, InvestigationContent]
    created_at_turn: int
    expiry_turn: int
    related_event_id: str  # ID of the public event this private info relates to
    government: GovernmentInfo  # Government info when this occurred
    phase: GamePhase  # Game phase when this occurred

@dataclass
class DiscussionMessage:
    player_id: str
    message: str
    timestamp: datetime

@dataclass
class GameEvent:
    event_id: str
    event_type: GameEventType
    turn_number: int
    phase: GamePhase
    timestamp: datetime
    actor_id: str
    action_details: Dict[str, Any]  # Keeps flexible for different event types
    justification: Optional[str] = None
    discussion: List[DiscussionMessage] = None
    related_events: List[str] = None  # IDs of related events

    def __post_init__(self):
        if self.discussion is None:
            self.discussion = []
        if self.related_events is None:
            self.related_events = []

@dataclass
class PlayerRole:
    """Information about a player's role, used for fascist knowledge"""
    id: str
    name: str
    is_hitler: bool

@dataclass
class GameState:
    """Complete game state returned by get_game_state"""
    turn: int
    phase: GamePhase
    liberal_policies: int
    fascist_policies: int
    president_id: str
    chancellor_id: Optional[str]
    last_government: Tuple[Optional[str], Optional[str]]
    players: Dict[str, Player]
    deck_size: int
    discard_size: int
    your_role: Optional[Role] = None
    events: Optional[List[GameEvent]] = None
    private_info: Optional[List[PrivateInfo]] = None
    fellow_fascists: Optional[List[PlayerRole]] = None  # Updated to use PlayerRole

@dataclass
class PendingVote:
    player_id: str
    vote: bool
    justification: str
    timestamp: datetime

@dataclass
class PolicyChoice:
    policy: PolicyCard
    justification: str
    claimed_policy: Optional[str]

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
        self.pending_policy_choice: Optional[PolicyChoice] = None
        
        self.current_policies: List[PolicyCard] = []
        
        # Logging and discussion state
        self.game_events: List[GameEvent] = []
        self.private_info: Dict[str, List[PrivateInfo]] = {pid: [] for pid in player_ids}
        
        self.current_turn = 0
        self.turn_phase = 0  # Tracks sub-phases within a turn
        self.last_event_id = 0  # For generating unique event IDs
        
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
    
    def _generate_event_id(self) -> str:
        self.last_event_id += 1
        return f"event_{self.current_turn}_{self.turn_phase}_{self.last_event_id}"

    def _log_event(self, 
                   event_type: GameEventType, 
                   actor_id: str, 
                   action_details: Dict[str, Any], 
                   justification: Optional[str] = None,
                   related_events: List[str] = None) -> GameEvent:
        event = GameEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            turn_number=self.current_turn,
            timestamp=datetime.now(),
            actor_id=actor_id,
            action_details=action_details,
            justification=justification,
            phase=self.phase,
            related_events=related_events or []
        )
        self.game_events.append(event)
        return event

    def add_discussion_message(self, 
                             event_index: int, 
                             player_id: str, 
                             message: str) -> bool:
        if 0 <= event_index < len(self.game_events):
            event = self.game_events[event_index]
            if len(event.discussion) < self.discussion_limit * len(self.get_active_players()): 
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
                        content: Union[PolicyChoiceContent, PolicyPeekContent, InvestigationContent],
                        related_event_id: str) -> None:
        """Add private information with all metadata"""
        info = PrivateInfo(
            recipient_id=recipient_id,
            info_type=info_type,
            content=content,
            created_at_turn=self.current_turn,
            expiry_turn=self.current_turn + 3,  # Most private info lasts 3 turns
            related_event_id=related_event_id,
            government=GovernmentInfo(
                president_id=self.get_president_id(),
                chancellor_id=self.chancellor_id,
                policy_counts={
                    "liberal": self.liberal_policies,
                    "fascist": self.fascist_policies
                }
            ),
            phase=self.phase
        )
        self.private_info[recipient_id].append(info)

    def get_visible_events(self, player_id: str) -> List[Dict]:
        """Convert GameEvent objects to dictionary format for the requesting player"""
        return [
            {
                "event_type": event.event_type.value,
                "turn_number": event.turn_number,
                "timestamp": event.timestamp.isoformat(),
                "actor": event.actor_id,  # Keep ID rather than name for consistency
                "details": event.action_details,
                "justification": event.justification,
                "discussion": event.discussion,
                "phase": event.phase.value if event.phase else None,
                "related_events": event.related_events
            }
            for event in self.game_events
        ]

    def get_private_info(self, player_id: str) -> List[PrivateInfo]:
        """Return unexpired private info for player"""
        return [
            info for info in self.private_info[player_id]
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

    def get_game_state(self, player_id: Optional[str] = None) -> GameState:
        """Get complete game state as dataclass"""
        state = GameState(
            turn=self.current_turn,
            phase=self.phase,
            liberal_policies=self.liberal_policies,
            fascist_policies=self.fascist_policies,
            president_id=self.get_president_id(),
            chancellor_id=self.chancellor_id,
            last_government=self.last_government,
            players=self.get_human_players(),
            deck_size=len(self.policy_deck),
            discard_size=len(self.discard_pile)
        )
        
        if player_id:
            player = self.players[player_id]
            state.your_role = player.role
            state.events = self.game_events
            state.private_info = self.get_private_info(player_id)
            
            # Add permanent role knowledge
            if player.role == Role.FASCIST:
                state.fellow_fascists = [
                    PlayerRole(
                        id=pid,
                        name=p.name,
                        is_hitler=p.role == Role.HITLER
                    )
                    for pid, p in self.get_human_players().items()
                    if p.role in [Role.FASCIST, Role.HITLER] and pid != player_id
                ]
            elif player.role == Role.HITLER and len(self.get_human_players()) <= 6:
                state.fellow_fascists = [
                    PlayerRole(
                        id=pid,
                        name=p.name,
                        is_hitler=False
                    )
                    for pid, p in self.get_human_players().items()
                    if p.role == Role.FASCIST
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

    def president_discard(self, index: int, claimed_policy: Optional[str], justification: str) -> bool:
        if self.phase != GamePhase.PRESIDENT_DISCARD or not 0 <= index < len(self.current_policies):
            return False

        # Log the public event
        policy_event = self._log_event(
            GameEventType.POLICY_ENACTED,
            self.get_president_id(),
            {
                "action": "discard",
                "claimed_policy": claimed_policy
            },
            justification
        )
        
        # Store private information about actual choice
        self.add_private_info(
            recipient_id=self.get_president_id(),
            info_type="policy_choice",
            content=PolicyChoiceContent(
                role="president",
                policies_seen=[p.value for p in self.current_policies],
                discarded=self.current_policies[index].value,
                claimed_discard=claimed_policy,
                remaining=[p.value for i, p in enumerate(self.current_policies) if i != index]
            ),
            related_event_id=policy_event.event_id
        )
        
        # Perform the actual discard
        discarded_policy = self.current_policies.pop(index)
        self.discard_pile.append(discarded_policy)
        
        self.phase = GamePhase.CHANCELLOR_DISCARD
        return True

    def chancellor_discard(self, index: int, claimed_policy: Optional[str], justification: str) -> Optional[str]:
        """
        Handle chancellor's policy selection with full metadata tracking.
        Returns: Enacted policy value or game result if game ends
        """
        if self.phase != GamePhase.CHANCELLOR_DISCARD or not 0 <= index < len(self.current_policies):
            return None
            
        # Get policies for game state update
        discarded_policy = self.current_policies[index]
        enacted_policy = self.current_policies[1 - index]
        
        # Log the public event
        chancellor_event = self._log_event(
            GameEventType.POLICY_ENACTED,
            self.chancellor_id,
            {
                "action": "enact",
                "enacted": enacted_policy.value,
                "claimed_policy": claimed_policy
            },
            justification,
            related_events=[self.game_events[-1].event_id]  # Link to president's event
        )
        
        # Store private information about actual choice
        self.add_private_info(
            recipient_id=self.chancellor_id,
            info_type="policy_choice",
            content=PolicyChoiceContent(
                role="chancellor",
                policies_seen=[p.value for p in self.current_policies],
                discarded=discarded_policy.value,
                claimed_discard=claimed_policy,
                remaining=[],  # Chancellor doesn't pass cards on
                enacted=enacted_policy.value
            ),
            related_event_id=chancellor_event.event_id
        )
        
        # Clear policies and update game state
        self.current_policies = []
        self.discard_pile.append(discarded_policy)
        
        # Update policy tracks
        if enacted_policy == PolicyCard.LIBERAL:
            self.liberal_policies += 1
        else:
            self.fascist_policies += 1
            
        # Check win conditions
        if self.liberal_policies >= 5:
            self.phase = GamePhase.GAME_OVER
            return "LIBERALS_WIN"
        elif self.fascist_policies >= 6:
            self.phase = GamePhase.GAME_OVER
            return "FASCISTS_WIN"
            
        # Handle next phase
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
        """Advance to next president and increment turn counters"""
        alive_players = [pid for pid, p in self.players.items() if p.is_alive]
        self.president_index = (self.president_index + 1) % len(alive_players)
        self.current_turn += 1
        self.turn_phase = 0
        
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
    
    def get_formatted_private_info(self, player_id: str) -> List[Dict]:
        """Get formatted private info with enhanced context"""
        return [
            {
                "type": info.info_type,
                "content": info.content,
                "turn_created": info.created_at_turn,
                "turns_remaining": info.expiry_turn - self.current_turn,
                "metadata": info.metadata,
                "related_event_id": info.related_event_id
            }
            for info in self.private_info[player_id]
            if info.expiry_turn >= self.current_turn
        ]