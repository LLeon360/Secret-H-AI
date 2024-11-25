from typing import List, Dict  
from input_handler import InputHandler, InputRequest, InputType, ResponseFormat, Responder, HumanResponder, ModelResponder  
from game_state import SecretHitler, Role, GamePhase, GameEventType  
import json

class GameManager:
    def __init__(self, player_ids: List[str], player_names: List[str], player_types: Dict[str, str],
                 discussion_limit: int = 1):
        self.game = SecretHitler(player_ids, player_names)
        self.game.discussion_limit = discussion_limit
        
        self.input_handler = InputHandler()
        self.current_event_index = len(self.game.game_events) - 1
        
        # Register responders for each player
        for pid in player_ids:
            if player_types[pid] == "human":
                self.input_handler.register_responder(pid, HumanResponder())
            else:
                self.input_handler.register_responder(pid, ModelResponder())

    def format_event(self, event: Dict) -> str:
        """Format a single event into a readable string"""
        def get_player_name(pid: str) -> str:
            return self.game.players[pid].name if pid != "system" else "System"
            
        def format_details(details: Dict) -> str:
            """Format event details into readable text"""
            if event['event_type'] == "game_start":
                return f"Game started with {details['player_count']} players"
            elif event['event_type'] == "chancellor_nomination":
                return f"nominated {get_player_name(details['nominee'])} as Chancellor"
            elif event['event_type'] == "vote_cast":
                vote_text = "Ja!" if details['vote'] else "Nein!"
                return f"voted {vote_text}"
            elif event['event_type'] == "election_result":
                return f"election for President {get_player_name(details['president_id'])} and Chancellor {get_player_name(details['chancellor_id'])}, Result {details['result']}"
            elif event['event_type'] == "policy_enacted":
                return f"enacted a {details['policy']} policy"
            elif event['event_type'] == "power_action":
                action = details['action']
                target = details.get('target')
                if target:
                    return f"used power '{action}' on {get_player_name(target)}"
                return f"used power '{action}'"
            else:
                return json.dumps(details)

        # Format the event header
        text = [f"\n{event['actor']} {format_details(event['details'])}"]
        
        # Add justification if present
        if event.get('justification'):
            text.append(f"Reasoning: \"{event['justification']}\"")
            
        # Add discussion if present
        if event.get('discussion'):
            text.append("\nDiscussion:")
            for msg in event['discussion']:
                text.append(f"  {get_player_name(msg['player_id'])}: \"{msg['message']}\"")
                
        return "\n".join(text)

    def format_context(self, player_id: str) -> str:
        """Format all relevant game information into a single string"""
        game_state = self.game.get_game_state(player_id)
        event_history = self.game.get_visible_events(player_id)
        player_name = game_state['players'][player_id]['name']
        
        # Get current nominations/government
        president_name = game_state['players'][game_state['president_id']]['name']
        chancellor_nominee = None
        if game_state['chancellor_id']:
            chancellor_nominee = game_state['players'][game_state['chancellor_id']]['name']
        
        context = [
            f"\n{'='*20} Game Status {'='*20}",
            f"\nYou are {player_name}",
            f"Your Role: {game_state['your_role'].title()}",
            f"Current Phase: {game_state['phase'].replace('_', ' ').title()}",
            
            f"\nPolicies Enacted:",
            f"Liberal Track: {'🔵' * game_state['liberal_policies']}{'⚪' * (5 - game_state['liberal_policies'])} "
            f"({game_state['liberal_policies']}/5)",
            f"Fascist Track: {'🔴' * game_state['fascist_policies']}{'⚪' * (6 - game_state['fascist_policies'])} "
            f"({game_state['fascist_policies']}/6)",
            
            "\nCurrent Government:"
        ]
        
        # Show current president
        context.append(f"President: {president_name}")
        
        # Show chancellor based on game phase
        if game_state['phase'] == 'voting':
            context.append(f"Nominated Chancellor: {chancellor_nominee}")
        elif chancellor_nominee and game_state['phase'] in ['president_discard', 'chancellor_discard']:
            context.append(f"Chancellor: {chancellor_nominee}")
            
        # Show last government if it exists
        if game_state.get('last_government'):
            pres_id, chanc_id = game_state['last_government']
            if pres_id and chanc_id:  # Check if both positions were filled
                context.append(
                    f"\nLast Government: "
                    f"{game_state['players'][pres_id]['name']} (P), "
                    f"{game_state['players'][chanc_id]['name']} (C)"
                )
            
        context.append("\nPlayers:")
        for pid, pinfo in game_state['players'].items():
            status_markers = []
            if pid == game_state['president_id']:
                status_markers.append("President")
            if pid == game_state['chancellor_id']:
                if game_state['phase'] == 'voting':
                    status_markers.append("Nominated")
                else:
                    status_markers.append("Chancellor")
            if not pinfo['is_alive']:
                status_markers.append("Dead")
            
            status = f" ({', '.join(status_markers)})" if status_markers else ""
            context.append(f"  • {pinfo['name']}{status}")
            
        if 'fascists' in game_state:
            context.append("\nYou know the following players are Fascists:")
            fascist_names = [game_state['players'][fid]['name'] for fid in game_state['fascists']]
            context.append("  • " + ", ".join(fascist_names))

        if game_state.get('private_info'):
            context.append("\nPrivate Information:")
            for info in game_state['private_info']:
                if info['type'] == 'policy_peek':
                    policies = info['content']['upcoming_policies']
                    context.append(f"  • You have seen the next {len(policies)} policies: {', '.join(policies)}")
                else:
                    context.append(f"  • {info['type']}: {json.dumps(info['content'])}")
            
        context.extend([
            f"\n{'='*20} Recent Events {'='*20}",
            *[self.format_event(event) for event in event_history[-5:]]
        ])
        
        return "\n".join(context)
    def handle_chancellor_nomination(self, president_id: str):
        """Handle chancellor nomination with new input system"""
        active_players = self.game.get_active_players()
        candidates = [
            pid for pid in active_players
            if pid != president_id and pid not in self.game.last_government
        ]
        
        request = InputRequest(
            input_type=InputType.CHANCELLOR_NOMINATION,
            player_id=president_id,
            context=self.format_context(president_id),
            prompt="Nominate a chancellor from the available candidates",
            response_format=ResponseFormat(
                schema={
                    "choice": "integer",
                    "justification": "string"
                },
                example={
                    "choice": 0,
                    "justification": "I trust this player to make good decisions"
                },
                required_fields=["choice", "justification"]
            ),
            options=[active_players[pid].name for pid in candidates]
        )
        
        response = self.input_handler.get_input(request)
        self.game.nominate_chancellor(
            president_id,
            candidates[response["choice"]],
            response["justification"]
        )
        self.current_event_index = len(self.game.game_events) - 1

    def handle_vote(self, player_id: str):
        """Handle voting with new input system"""
        request = InputRequest(
            input_type=InputType.VOTE,
            player_id=player_id,
            context=self.format_context(player_id),
            prompt="Vote on the proposed government",
            response_format=ResponseFormat(
                schema={
                    "choice": "integer",
                    "justification": "string"
                },
                example={
                    "choice": 0,
                    "justification": "I believe this government will make good decisions"
                },
                required_fields=["choice", "justification"]
            ),
            options=["Ja!", "Nein!"]
        )
        
        response = self.input_handler.get_input(request)
        return self.game.vote(player_id, response["choice"] == 0, response["justification"])

    def handle_policy_selection(self, player_id: str, is_president: bool):
        """Handle policy selection for both president and chancellor"""
        policies = self.game.current_policies
        action_type = "discard" if is_president else "enact"
        
        request = InputRequest(
            input_type=InputType.POLICY_SELECTION,
            player_id=player_id,
            context=self.format_context(player_id),
            prompt=f"Choose a policy to {action_type}",
            response_format=ResponseFormat(
                schema={"choice": "integer"},
                example={"choice": 0},
                required_fields=["choice"]
            ),
            options=[f"Policy: {policy.value}" for policy in policies]
        )
        
        response = self.input_handler.get_input(request)
        if is_president:
            return self.game.president_discard(response["choice"])
        else:
            return self.game.chancellor_discard(response["choice"])

    def handle_power_action(self, president_id: str):
        """Handle presidential power actions"""
        # This would need to be expanded based on the specific power actions
        # available at different fascist policy counts
        request = InputRequest(
            input_type=InputType.POWER_ACTION,
            player_id=president_id,
            context=self.format_context(president_id),
            prompt="Execute your presidential power",
            response_format=ResponseFormat(
                schema={
                    "action": "string",
                    "target": "string"
                },
                example={
                    "action": "investigate",
                    "target": "player2"
                },
                required_fields=["action", "target"]
            ),
            options=[]  # Would be populated based on available powers
        )
        
        response = self.input_handler.get_input(request)
        return self.game.execute_power_action(response["action"], response["target"])

    def handle_discussion(self, initiating_player_id: str):
        """Handle discussion for all players"""
        active_players = list(self.game.get_active_players().keys())
        messages_per_player = self.game.discussion_limit // len(active_players)
        
        if messages_per_player < 1:
            messages_per_player = 0
            
        player_order = (
            active_players[active_players.index(initiating_player_id):] +
            active_players[:active_players.index(initiating_player_id)]
        )
        
        for _ in range(messages_per_player):
            for player_id in player_order:
                request = InputRequest(
                    input_type=InputType.DISCUSSION,
                    player_id=player_id,
                    context=self.format_context(player_id),
                    prompt="Would you like to add to the discussion?",
                    response_format=ResponseFormat(
                        schema={
                            "confirmation": "boolean",
                            "message": "string"
                        },
                        example={
                            "confirmation": True,
                            "message": "I think we should be careful about this decision"
                        },
                        required_fields=["confirmation", "message"]
                    ),
                    options=[]
                )
                
                response = self.input_handler.get_input(request)
                if response["confirmation"]:
                    self.game.add_discussion_message(
                        self.current_event_index,
                        player_id,
                        response["message"]
                    )

    def play_turn(self):
        """Process one game turn"""
        current_phase = self.game.phase
        president_id = self.game.get_president_id()

        try:
            if current_phase == GamePhase.NOMINATING_CHANCELLOR:
                # Get valid chancellor candidates
                active_players = self.game.get_active_players()
                candidates = [
                    pid for pid in active_players
                    if (pid != president_id and 
                        pid not in (self.game.last_government if self.game.last_government else ()))
                ]
                
                if not candidates:
                    print("No valid chancellor candidates!")
                    return
                
                self.handle_chancellor_nomination(president_id)
                self.handle_discussion(president_id)

            elif current_phase == GamePhase.VOTING:
                active_players = list(self.game.get_active_players().keys())
                election_result = None
                
                # Collect votes from all players
                for player_id in active_players:
                    result = self.handle_vote(player_id)
                    if result is not None:  # Last vote cast
                        election_result = result
                        break  # Exit after final vote is cast
                
                # Only handle discussion if election passed
                if election_result:
                    self.current_event_index = len(self.game.game_events) - 1
                    self.handle_discussion(president_id)

            elif current_phase == GamePhase.PRESIDENT_DISCARD:
                self.handle_policy_selection(president_id, is_president=True)

            elif current_phase == GamePhase.CHANCELLOR_DISCARD:
                result = self.handle_policy_selection(self.game.chancellor_id, is_president=False)
                if result:
                    self.current_event_index = len(self.game.game_events) - 1
                    self.handle_discussion(self.game.chancellor_id)

            elif current_phase == GamePhase.POWER_ACTION:
                self.handle_power_action(president_id)
                self.current_event_index = len(self.game.game_events) - 1
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
                request = InputRequest(
                    input_type=InputType.CONFIRMATION,
                    player_id="system",
                    context="Game interrupted",
                    prompt="Do you want to quit?",
                    response_format=ResponseFormat(
                        schema={"confirmation": "boolean"},
                        example={"confirmation": True},
                        required_fields=["confirmation"]
                    ),
                    options=[]
                )
                response = self.input_handler.get_input(request)
                if response["confirmation"]:
                    return
                    
        print("\nGame Over!")
        print(self.format_context("system"))
