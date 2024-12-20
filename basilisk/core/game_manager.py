from typing import List, Dict, Callable
from core.input_handler import (
	InputHandler
)
from responders.base import (
	InputRequest, ExampleResponse, InputField, InputType, Responder
)
from core.game_state import (
	SecretHitler, Role, GamePhase, GameEventType, GameEvent,
	PolicyChoiceContent, PolicyPeekContent, InvestigationContent,
	PrivateInfo, GameState, PlayerRole, DiscussionMessage
)
import json
from datetime import datetime

# Type for responder creation functions 
ResponderCreator = Callable[[], Responder]

class GameManager:
	def __init__(self, 
				player_configs: List[Dict[str, str]],
				responder_creators: Dict[str, ResponderCreator],
				discussion_limit: int = 2):
		"""Initialize game manager with players and responders.
		
		Args:
			player_configs: List of dicts with 'name' and 'type' keys for each player
			responder_creators: Dict mapping player types to responder creation functions
			discussion_limit: Maximum discussion messages per player
		"""
		# Generate player IDs and names
		self.player_ids = [f"p{i+1}" for i in range(len(player_configs))]
		self.player_names = [p["name"] for p in player_configs]
		
		# Initialize game state
		self.game = SecretHitler(self.player_ids, self.player_names)
		self.game.discussion_limit = discussion_limit
		self.input_handler = InputHandler()
	   
		# Setup responders
		for pid, config in zip(self.player_ids, player_configs):
				player_type = config["type"]
				if player_type not in responder_creators:
					raise ValueError(f"Unknown player type: {player_type}")
					
				responder = responder_creators[player_type]()
				self.input_handler.register_responder(pid, responder)

	def handle_chancellor_nomination(self, president_id: str):
		"""Handle chancellor nomination"""
		active_players = self.game.get_active_players()
		candidates = [
			pid for pid in active_players
			if pid != president_id and pid not in self.game.last_government
		]
		
		if not candidates:
			return False
			
		fields = [
			InputField(
				name="candidate",
				field_type="choice",
				prompt="Choose a chancellor candidate:",
				options=[active_players[pid].name for pid in candidates],
				required=True
			),
			InputField(
				name="justification",
				field_type="text",
				prompt="Explain your nomination:",
				required=True
			)
		]
		
		request = InputRequest(
			input_type=InputType.CHANCELLOR_NOMINATION,
			player_id=president_id,
			context=self.game.get_game_state(president_id),
			fields=fields,
			example=ExampleResponse(
				values={
					"candidate": 0,
					"justification": "I trust this player's judgment because..."
				}
			)
		)
		
		response = self.input_handler.get_input(request)
		return self.game.nominate_chancellor(
			president_id,
			candidates[response["candidate"]],
			response["justification"]
		)

	def handle_vote(self, player_id: str):
		"""Handle voting on proposed government"""
		fields = [
			InputField(
				name="vote",
				field_type="choice",
				prompt="Vote on the proposed government:",
				options=["Ja!", "Nein!"],
				required=True
			),
			InputField(
				name="justification",
				field_type="text",
				prompt="Explain your vote:",
				required=True
			)
		]
		
		request = InputRequest(
			input_type=InputType.VOTE,
			player_id=player_id,
			context=self.game.get_game_state(player_id),
			fields=fields,
			example=ExampleResponse(
				values={
					"vote": 0,
					"justification": "I support this government because..."
				}
			)
		)
		
		response = self.input_handler.get_input(request)
		return self.game.vote(
			player_id,
			response["vote"] == 0,  # Convert to boolean
			response["justification"]
		)
		
	def handle_policy_selection(self, player_id: str, is_president: bool):
		"""Handle policy selection for both president and chancellor"""
		policies = self.game.current_policies
		action_type = "discard"
		
		fields = [
			InputField(
				name="policy",
				field_type="choice",
				prompt=f"Choose a policy to {action_type}:",
				options=[f"Policy: {policy.value}" for policy in policies],
				required=True
			),
			InputField(
				name="claimed_policy",
				field_type="choice",
				prompt="What policy will you claim to have discarded?",
				options=["liberal", "fascist", "undisclosed"],
				required=False,
				default=2  # Default to undisclosed
			),
			InputField(
				name="justification",
				field_type="text",
				prompt="Explain your choice:",
				required=True
			)
		]
		
		request = InputRequest(
			input_type=InputType.POLICY_SELECTION,
			player_id=player_id,
			context=self.game.get_game_state(player_id),
			fields=fields,
			example=ExampleResponse(
				values={
					"policy": 0,
					"claimed_policy": 2,
					"justification": "This advances our team's goals because..."
				}
			)
		)
		
		response = self.input_handler.get_input(request)
		
		if is_president:
			return self.game.president_discard(
				response["policy"],
				response["claimed_policy"],
				response["justification"]
			)
		else:
			return self.game.chancellor_discard(
				response["policy"],
				response["claimed_policy"],
				response["justification"]
			)

	def handle_power_action(self, president_id: str):
		"""Handle presidential power actions"""
		game_state = self.game.get_game_state(president_id)
		
		# First get power choice
		action_fields = [
			InputField(
				name="action",
				field_type="choice",
				prompt="Choose a presidential power to use:",
				options=["investigate", "peek", "special_election", "execute"],
				required=True
			),
			InputField(
				name="justification",
				field_type="text",
				prompt="Explain your choice:",
				required=True
			)
		]
		
		power_request = InputRequest(
			input_type=InputType.POWER_ACTION,
			player_id=president_id,
			context=self.game.get_game_state(president_id),
			fields=action_fields,
			example=ExampleResponse(
				values={
					"action": "investigate",
					"justification": "Need to verify loyalty"
				}
			)
		)
		
		power_response = self.input_handler.get_input(power_request)
		action = power_response["action"]
		
		# If power requires target, get target selection
		if action in ["investigate", "execute", "special_election"]:
			# Get valid targets based on action type
			valid_targets = [
				pid for pid, player in game_state.players.items()
				if player.is_alive and pid != president_id and (
					action != "investigate" or
					not any(isinstance(info.content, InvestigationContent) and 
						   info.content.target_id == pid
						   for info in game_state.private_info or [])
				)
			]
			
			target_fields = [
				InputField(
					name="target",
					field_type="choice",
					prompt=f"Choose a player to {action}:",
					options=[game_state.players[pid].name for pid in valid_targets],
					required=True
				)
			]
			
			target_request = InputRequest(
				input_type=InputType.POWER_ACTION,
				player_id=president_id,
				context=self.game.get_game_state(president_id),
				fields=target_fields,
				example=ExampleResponse(
					values={
						"target": 0
					}
				)
			)
			
			target_response = self.input_handler.get_input(target_request)
			target_id = valid_targets[target_response["target"]]
			
			return self.game.execute_power_action(action, target_id)
		else:
			return self.game.execute_power_action(action)

	def handle_discussion(self, initiating_player_id: str):
		"""Handle discussion phase"""
		active_players = list(self.game.get_active_players().keys())
		messages_per_player = self.game.discussion_limit 
		
		if messages_per_player < 1:
			return
			
		# Order players starting with initiator
		player_order = (
			active_players[active_players.index(initiating_player_id):] +
			active_players[:active_players.index(initiating_player_id)]
		)
		
		discussion_fields = [
			InputField(
				name="want_to_speak",
				field_type="boolean",
				prompt="Would you like to add to the discussion?",
				required=True
			),
			InputField(
				name="message",
				field_type="text",
				prompt="Enter your message:",
				required=True
			)
		]
		
		for _ in range(messages_per_player):
			for player_id in player_order:
				request = InputRequest(
					input_type=InputType.DISCUSSION,
					player_id=player_id,
					context=self.game.get_game_state(player_id),
					fields=discussion_fields,
					example=ExampleResponse(
						values={
							"want_to_speak": True,
							"message": "I think..."
						}
					)
				)
				
				response = self.input_handler.get_input(request)
				if response["want_to_speak"]:
					self.game.add_discussion_message(
						len(self.game.game_events) - 1,  # Add to last event
						player_id,
						response["message"]
					)

	def play_turn(self):
		"""Process one game turn"""
		current_phase = self.game.phase
		president_id = self.game.get_president_id()

		try:
			if current_phase == GamePhase.NOMINATING_CHANCELLOR:
				# Handle chancellor nomination
				if self.handle_chancellor_nomination(president_id):
					self.handle_discussion(president_id)

			elif current_phase == GamePhase.VOTING:
				# Handle voting
				active_players = list(self.game.get_active_players().keys())
				election_result = None
				
				for player_id in active_players:
					result = self.handle_vote(player_id)
					if result is not None:  # Last vote cast
						election_result = result
						break
				
				if election_result:
					self.handle_discussion(president_id)

			elif current_phase == GamePhase.PRESIDENT_DISCARD:
				self.handle_policy_selection(president_id, is_president=True)

			elif current_phase == GamePhase.CHANCELLOR_DISCARD:
				result = self.handle_policy_selection(self.game.chancellor_id, is_president=False)
				if result:
					self.handle_discussion(self.game.chancellor_id)
				else:
					raise ValueError("Chancellor discard failed")

			elif current_phase == GamePhase.POWER_ACTION:
				self.handle_power_action(president_id)
				self.handle_discussion(president_id)

		except Exception as e:
			print(f"Error in play_turn: {str(e)}")
			raise

	def play_game(self):
		"""Main game loop"""
		print("\nStarting Secret Hitler...")
		print("=======================")
		
		while self.game.phase != GamePhase.GAME_OVER:
			try:
				self.play_turn()
			except KeyboardInterrupt:
				quit_fields = [
					InputField(
						name="quit",
						field_type="boolean",
						prompt="Do you want to quit?",
						required=True
					)
				]
				
				request = InputRequest(
					input_type=InputType.CONFIRMATION,
					player_id="system",
					context="Game interrupted",
					fields=quit_fields,
					example=ExampleResponse(
						values={
							"quit": True
						}
					)
				)
				
				response = self.input_handler.get_input(request)
				if response["quit"]:
					return
					
		print("\nGame Over!")
		print("==========")
		