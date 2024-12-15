from typing import Any, Dict

from ..base import Responder, InputRequest

class HumanResponder(Responder):
    """Human responder implementation with console interaction"""
    
    def get_response(self, request: InputRequest) -> Dict[str, Any]:
        """Get response through console interaction"""
        print("\n=== Input Request ===")
        print("\nContext:")
        print(request.context)
        
        response = {}
        
        for field in request.fields:
            print(f"\n{field.prompt}")
            
            if field.field_type == "choice" and field.options:
                print("\nOptions:")
                for i, option in enumerate(field.options, 1):
                    print(f"{i}. {option}")
                
                while True:
                    if not field.required:
                        print("(Press Enter to skip)")
                    try:
                        value = input("\nEnter your choice (number): ").strip()
                        if not field.required and not value:
                            response[field.name] = field.default
                            break
                        choice = int(value) - 1
                        if 0 <= choice < len(field.options):
                            response[field.name] = choice
                            break
                        print("Invalid choice, try again.")
                    except ValueError:
                        print("Please enter a number.")
                        
            elif field.field_type == "boolean":
                while True:
                    if not field.required:
                        print("(Press Enter to skip)")
                    value = input(f"\nEnter choice (y/n): ").lower().strip()
                    if not field.required and not value:
                        response[field.name] = field.default
                        break
                    if value in ['y', 'n']:
                        response[field.name] = value == 'y'
                        break
                    print("Invalid input. Please enter 'y' or 'n'.")
                    
            elif field.field_type == "text":
                while True:
                    if not field.required:
                        print("(Press Enter to skip)")
                    value = input(f"\nEnter your response: ").strip()
                    if not value:
                        if not field.required:
                            response[field.name] = field.default
                            break
                        elif field.required:
                            print("This field is required.")
                            continue
                    else:
                        response[field.name] = value
                        break
        
        return response