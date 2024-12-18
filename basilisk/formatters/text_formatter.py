from typing import Dict, List, Optional
from core.game_state import (
    GameState, GameEvent, PrivateInfo, PolicyChoiceContent,
    PolicyPeekContent, InvestigationContent, GameEventType,
    GamePhase, Role, Player
)

class GameStateTextFormatter:
    """Utility class for formatting game state as text"""
    
    @staticmethod
    def _get_policy_from_index(index: int) -> str:
        """Get policy string from index"""
        policies = ["liberal", "fascist"]
        if 0 <= index < len(policies):
            return policies[index]
        return "undisclosed"
    
    @classmethod
    def format_private_info(cls, info: PrivateInfo, players: Dict[str, Player], current_turn: int) -> str:
        """Format a single piece of private information into readable text"""
        turns_ago = current_turn - info.created_at_turn
        turns_remaining = info.expiry_turn - current_turn
        
        formatted = []
        
        if isinstance(info.content, PolicyChoiceContent):
            content = info.content
            gov = info.government
            claimed_discard = cls._get_policy_from_index(content.claimed_discard)
            if content.role == "president":
                formatted.extend([
                    f"\nPolicy choice as President ({turns_ago} turns ago):",
                    f"Government: You as President with {players[gov.chancellor_id].name} as Chancellor",
                    f"Policy counts were: Liberal {gov.policy_counts['liberal']}, Fascist {gov.policy_counts['fascist']}",
                    f"You saw: {', '.join(content.policies_seen)}",
                    f"You discarded: {content.discarded}",
                    f"You claimed to discard: {claimed_discard}",
                    f"You passed: {', '.join(content.remaining)} to Chancellor"
                ])
            else:  # chancellor
                formatted.extend([
                    f"\nPolicy choice as Chancellor ({turns_ago} turns ago):",
                    f"Government: {players[gov.president_id].name} as President with you as Chancellor",
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
            target_name = players[info.content.target_id].name
            formatted.extend([
                f"\nInvestigation result ({turns_ago} turns ago):",
                f"You investigated {target_name}",
                f"Their party membership was: {info.content.party_membership}"
            ])
            
        if turns_remaining > 0:
            formatted.append(f"(This information expires in {turns_remaining} turns)")
            
        return "\n".join(formatted)

    @classmethod
    def format_event(cls, event: GameEvent, players: Dict[str, Player]) -> str:
        """Format a GameEvent into readable text"""
        def get_player_name(pid: str) -> str:
            return players[pid].name if pid != "system" else "System"
            
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
            claimed_discard = cls._get_policy_from_index(claimed)
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
            main_text = f"{turn_info}{str(event.action_details)}"

        # Compile full text with justification and discussion
        text = [f"\n{main_text}"]
        
        if event.justification:
            text.append(f"Reasoning: \"{event.justification}\"")
            
        if event.discussion:
            text.append("\nDiscussion:")
            for msg in event.discussion:
                text.append(f"  {get_player_name(msg['player_id'])}: \"{msg['message']}\"")
                
        return "\n".join(text)

    @classmethod
    def format_state(cls, state: GameState, player_id: str) -> str:
        """Format complete game state into readable text"""
        context = [
            f"\n{'='*20} Game Status {'='*20}",
            f"\nTurn {state.turn}",
            f"You are {state.players[player_id].name}",
            f"Your Role: {state.your_role.value.title()}",
            f"Current Phase: {state.phase.value.replace('_', ' ').title()}"
        ]
        
        # Add policy tracks
        context.extend([
            f"\nPolicies Enacted:",
            f"Liberal Track: {'🔵' * state.liberal_policies}{'⚪' * (5 - state.liberal_policies)} "
            f"({state.liberal_policies}/5)",
            f"Fascist Track: {'🔴' * state.fascist_policies}{'⚪' * (6 - state.fascist_policies)} "
            f"({state.fascist_policies}/6)"
        ])
        
        # Add government information
        context.append("\nCurrent Government:")
        president_name = state.players[state.president_id].name
        context.append(f"President: {president_name}")
        
        if state.chancellor_id:
            chancellor_name = state.players[state.chancellor_id].name
            if state.phase == GamePhase.VOTING:
                context.append(f"Nominated Chancellor: {chancellor_name}")
            elif state.phase in [GamePhase.PRESIDENT_DISCARD, GamePhase.CHANCELLOR_DISCARD]:
                context.append(f"Chancellor: {chancellor_name}")
        
        # Show last government
        if state.last_government != (None, None):
            pres_id, chanc_id = state.last_government
            context.append(
                f"\nLast Government: "
                f"{state.players[pres_id].name} (P), "
                f"{state.players[chanc_id].name} (C)"
            )
        
        # Add player list with status
        context.append("\nPlayers:")
        for pid, player in state.players.items():
            status_markers = []
            if pid == state.president_id:
                status_markers.append("President")
            if pid == state.chancellor_id:
                if state.phase == GamePhase.VOTING:
                    status_markers.append("Nominated")
                elif state.phase == GamePhase.NOMINATING_CHANCELLOR:
                    status_markers.append("Previously Nominated as Chancellor")
                else:
                    status_markers.append("Chancellor")
            if not player.is_alive:
                status_markers.append("Dead")
            
            status = f" ({', '.join(status_markers)})" if status_markers else ""
            context.append(f"  • {player.name}{status}")
        
        # Add fascist knowledge
        if state.fellow_fascists:
            if state.your_role == Role.FASCIST:
                context.append("\nAs a Fascist, you know:")
                for fascist in state.fellow_fascists:
                    if fascist.is_hitler:
                        context.append(f"  • {fascist.name} is Hitler")
                    else:
                        context.append(f"  • {fascist.name} is a fellow Fascist")
            elif state.your_role == Role.HITLER:
                if len(state.players) <= 6:  # 5-6 player game
                    context.append("\nAs Hitler in a 5-6 player game, you know your fellow Fascists:")
                    fascist_names = [f.name for f in state.fellow_fascists]
                    context.append("  • " + ", ".join(fascist_names))
                else:
                    context.append("\nAs Hitler in a 7+ player game, you do not know who your fellow Fascists are")
        
        # Add private information
        if state.private_info:
            context.append("\nPrivate Information:")
            for info in state.private_info:
                context.append(cls.format_private_info(info, state.players, state.turn))
        
        # Add recent events
        context.extend([
            f"\n{'='*20} Recent Events {'='*20}"
        ])
        
        if state.events:
            context.extend([cls.format_event(event, state.players) for event in state.events[-15:]])
        
        return "\n".join(context)