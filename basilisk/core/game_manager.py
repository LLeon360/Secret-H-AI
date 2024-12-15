from typing import List, Dict, Callable
from core.input_handler import (
	InputHandler
)
from responders.base import (
	InputRequest, ExampleResponse, InputField, InputType, Responder
)
from .game_state import (
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
	
	def get_policy_from_index(self, index: int) -> str:
		"""Get policy string from index"""
		policies = ["liberal", "fascist"]
		if 0 <= index < len(policies):
			return policies[index]
		return "undisclosed"
	
	def format_private_info(self, info: PrivateInfo) -> str:
		"""Format a single piece of private information into readable text"""
		turns_ago = self.game.current_turn - info.created_at_turn
		turns_remaining = info.expiry_turn - self.game.current_turn
		
		formatted = []
		
		if isinstance(info.content, PolicyChoiceContent):
			content = info.content
			gov = info.government
			claimed_discard = self.get_policy_from_index(content.claimed_discard)
			if content.role == "president":
				formatted.extend([
					f"\nPolicy choice as President ({turns_ago} turns ago):",
					f"Government: You as President with {self.game.players[gov.chancellor_id].name} as Chancellor",
					f"Policy counts were: Liberal {gov.policy_counts['liberal']}, Fascist {gov.policy_counts['fascist']}",
					f"You saw: {', '.join(content.policies_seen)}",
					f"You discarded: {content.discarded}",
					f"You claimed to discard: {claimed_discard}",
					f"You passed: {', '.join(content.remaining)} to Chancellor"
				])
			else:  # chancellor
				formatted.extend([
					f"\nPolicy choice as Chancellor ({turns_ago} turns ago):",
					f"Government: {self.game.players[gov.president_id].name} as President with you as Chancellor",
					f"Policy counts were: Liberal {gov.policy_counts['liberal']}, Fascist {gov.policy_counts['fascist']}",
					f"You received: {', '.join(content.policies_seen)}",
					f"You discarded: {content.discarded}",
					f"You claimed to discard: {claimed_discard}",
					f"You enacted: {content.enacted}"
				])
				
		elif isinstance(info.content, PolicyPeekContent):
			formatted.extend([
				f"\nPolicy peek ({turns_ago} turns ago):",
				f"As President, you looked at the top policies:",
				f"You saw: {', '.join(info.content.upcoming_policies)}"
			])
			
		elif isinstance(info.content, InvestigationContent):
			target_name = self.game.players[info.content.target_id].name
			formatted.extend([
				f"\nInvestigation result ({turns_ago} turns ago):",
				f"You investigated {target_name}",
				f"Their party membership was: {info.content.party_membership}"
			])
			
		if turns_remaining > 0:
			formatted.append(f"(This information expires in {turns_remaining} turns)")
			
		return "\n".join(formatted)

	def format_event(self, event: GameEvent) -> str:
		"""Format a GameEvent into readable text"""
		def get_player_name(pid: str) -> str:
			return self.game.players[pid].name if pid != "system" else "System"
			
		turn_info = f"[Turn {event.turn_number}] "
		
		# Format main event details
		if event.event_type == GameEventType.GAME_START:
			main_text = f"{turn_info}Game started with {event.action_details['player_count']} players"
			
		elif event.event_type == GameEventType.CHANCELLOR_NOMINATION:
			nominator = get_player_name(event.actor_id)
			nominee = get_player_name(event.action_details['nominee'])
			main_text = f"{turn_info}{nominator} nominated {nominee} as Chancellor"
			
		elif event.event_type == GameEventType.VOTE:
			voter = get_player_name(event.actor_id)
			vote_text = "Ja!" if event.action_details['vote'] else "Nein!"
			main_text = f"{turn_info}{voter} voted {vote_text}"
			
		elif event.event_type == GameEventType.ELECTION_RESULT:
			president = get_player_name(event.action_details['president_id'])
			chancellor = get_player_name(event.action_details['chancellor_id'])
			result = event.action_details['result']
			main_text = f"{turn_info}Election for President {president} and Chancellor {chancellor}: {result}"
			
		elif event.event_type == GameEventType.POLICY_ENACTED:
			claimed = event.action_details.get('claimed_policy')
			claimed_discard = self.get_policy_from_index(claimed)
			actor = get_player_name(event.actor_id)
			if event.action_details['action'] == "discard":
				main_text = f"{turn_info}President {actor} claims to have discarded a {claimed_discard} policy"
			else:  # enact
				enacted = event.action_details['enacted']
				main_text = f"{turn_info}Chancellor {actor} enacted a {enacted} policy (claims to have discarded a {claimed_discard} policy)"
					
		elif event.event_type == GameEventType.POWER_ACTION:
			actor = get_player_name(event.actor_id)
			action = event.action_details['action']
			if target_id := event.action_details.get('target'):
				target = get_player_name(target_id)
				main_text = f"{turn_info}{actor} used power '{action}' on {target}"
			else:
				main_text = f"{turn_info}{actor} used power '{action}'"
				
		elif event.event_type == GameEventType.GAME_END:
			main_text = f"{turn_info}Game Over: {event.action_details['result']}"
			
		else:
			main_text = f"{turn_info}{json.dumps(event.action_details)}"

		# Compile full text with justification and discussion
		text = [f"\n{main_text}"]
		
		if event.justification:
			text.append(f"Reasoning: \"{event.justification}\"")
			
		if event.discussion:
			text.append("\nDiscussion:")
			for msg in event.discussion:
				text.append(f"  {get_player_name(msg["player_id"])}: \"{msg["message"]}\"")
				
		return "\n".join(text)

	def format_context(self, player_id: str) -> str:
		"""Format complete game state into readable text"""
		game_state = self.game.get_game_state(player_id)
		
		context = [
			f"\n{'='*20} Game Status {'='*20}",
			f"\nTurn {game_state.turn}",
			f"You are {game_state.players[player_id].name}",
			f"Your Role: {game_state.your_role.value.title()}",
			f"Current Phase: {game_state.phase.value.replace('_', ' ').title()}"
		]
		
		# Add policy tracks
		context.extend([
			f"\nPolicies Enacted:",
			f"Liberal Track: {'🔵' * game_state.liberal_policies}{'⚪' * (5 - game_state.liberal_policies)} "
			f"({game_state.liberal_policies}/5)",
			f"Fascist Track: {'🔴' * game_state.fascist_policies}{'⚪' * (6 - game_state.fascist_policies)} "
			f"({game_state.fascist_policies}/6)"
		])
		
		# Add government information
		context.append("\nCurrent Government:")
		president_name = game_state.players[game_state.president_id].name
		context.append(f"President: {president_name}")
		
		if game_state.chancellor_id:
			chancellor_name = game_state.players[game_state.chancellor_id].name
			if game_state.phase == GamePhase.VOTING:
				context.append(f"Nominated Chancellor: {chancellor_name}")
			elif game_state.phase in [GamePhase.PRESIDENT_DISCARD, GamePhase.CHANCELLOR_DISCARD]:
				context.append(f"Chancellor: {chancellor_name}")
		
		# Show last government
		if game_state.last_government != (None, None):
			pres_id, chanc_id = game_state.last_government
			context.append(
				f"\nLast Government: "
				f"{game_state.players[pres_id].name} (P), "
				f"{game_state.players[chanc_id].name} (C)"
			)
		
		# Add player list with status
		context.append("\nPlayers:")
		for pid, player in game_state.players.items():
			status_markers = []
			if pid == game_state.president_id:
				status_markers.append("President")
			if pid == game_state.chancellor_id:
				if game_state.phase == GamePhase.VOTING:
					status_markers.append("Nominated")
				elif game_state.phase == GamePhase.NOMINATING_CHANCELLOR:
					status_markers.append("Previously Nominated as Chancellor")
				else:
					status_markers.append("Chancellor")
			if not player.is_alive:
				status_markers.append("Dead")
			
			status = f" ({', '.join(status_markers)})" if status_markers else ""
			context.append(f"  • {player.name}{status}")
		
		# Add fascist knowledge
		if game_state.fellow_fascists:
			if game_state.your_role == Role.FASCIST:
				context.append("\nAs a Fascist, you know:")
				for fascist in game_state.fellow_fascists:
					if fascist.is_hitler:
						context.append(f"  • {fascist.name} is Hitler")
					else:
						context.append(f"  • {fascist.name} is a fellow Fascist")
			elif game_state.your_role == Role.HITLER:
				if len(game_state.players) <= 6:  # 5-6 player game
					context.append("\nAs Hitler in a 5-6 player game, you know your fellow Fascists:")
					fascist_names = [f.name for f in game_state.fellow_fascists]
					context.append("  • " + ", ".join(fascist_names))
				else:
					context.append("\nAs Hitler in a 7+ player game, you do not know who your fellow Fascists are")
		
		# Add private information
		if game_state.private_info:
			context.append("\nPrivate Information:")
			for info in game_state.private_info:
				context.append(self.format_private_info(info))
		
		# Add recent events
		context.extend([
			f"\n{'='*20} Recent Events {'='*20}"
		])
		
		if game_state.events:
			context.extend([self.format_event(event) for event in game_state.events[-15:]])
		
		return "\n".join(context)

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
			context=self.format_context(president_id),
			fields=fields,
			example=ExampleResponse(
				values={
					"candidate": 0,
					"justification": "I trust this player's judgment"
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
			context=self.format_context(player_id),
			fields=fields,
			example=ExampleResponse(
				values={
					"vote": 0,
					"justification": "I support this government"
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
			context=self.format_context(player_id),
			fields=fields,
			example=ExampleResponse(
				values={
					"policy": 0,
					"claimed_policy": 2,
					"justification": "This advances our team's goals"
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
			context=self.format_context(president_id),
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
				context=self.format_context(president_id),
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
					context=self.format_context(player_id),
					fields=discussion_fields,
					example=ExampleResponse(
						values={
							"want_to_speak": True,
							"message": "I think we should be careful about this decision"
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
		print(self.format_context("system"))