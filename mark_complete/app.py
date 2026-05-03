from rich.console import Console
from dotenv import load_dotenv
from openai import OpenAI
import json

load_dotenv(override=True)

def show(text):
    try:
        Console().print(text)
    except Exception:
        print(text)

create_todos_json = {
    "name": "create_todos",
    "description": "Add new todos from a list of descriptions and return the full list",
    "parameters": {
        "type": "object",
        "properties": {
            "descriptions": {
                'type': 'array',
                'items': {'type': 'string'},
                'title': 'Descriptions'
                }
            },
        "required": ["descriptions"],
        "additionalProperties": False
    }
}

mark_complete_json = {
    "name": "mark_complete",
    "description": "Mark complete the todo at the given position (starting from 1) and return the full list",
    "parameters": {
        'properties': {
            'index': {
                'description': 'The 1-based index of the todo to mark as complete',
                'title': 'Index',
                'type': 'integer'
                },
            'completion_notes': {
                'description': 'Notes about how you completed the todo in rich console markup',
                'title': 'Completion Notes',
                'type': 'string'
                }
            },
        'required': ['index', 'completion_notes'],
        'type': 'object',
        'additionalProperties': False
    }
}


tools = [{"type": "function", "function": create_todos_json},
        {"type": "function", "function": mark_complete_json}]

class MarkCompleteTool:
    def __init__(self):
        self.todos = []
        self.completed = []
        self.openai = OpenAI()
        
    def handle_tool_calls(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
        
    def get_todo_report(self) -> str:
        result = ""
        for index, todo in enumerate(self.todos):
            if self.completed[index]:
                result += f"Todo #{index + 1}: [green][strike]{todo}[/strike][/green]\n"
            else:
                result += f"Todo #{index + 1}: {todo}\n"
        show(result)
        return result
        
    def create_todos(self, descriptions: list[str]) -> str:
        self.todos.extend(descriptions)
        self.completed.extend([False] * len(descriptions))
        return self.get_todo_report()

    def mark_complete(self, index: int, completion_notes: str) -> str:
        if 1 <= index <= len(self.todos):
            self.completed[index - 1] = True
        else:
            return "No todo at this index."
        Console().print(completion_notes)
        return self.get_todo_report()
    
    def loop(self, messages):
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-5.2", messages=messages, tools=tools, reasoning_effort="none")
            finish_reason = response.choices[0].finish_reason
            if finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_calls(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        show(response.choices[0].message.content)
            
        
if __name__ == "__main__":
    mark_complete_tool = MarkCompleteTool()
    
    # Example of how to call the tool directly without going through the LLM, which is useful for testing the tool logic.:
    mark_complete_tool.create_todos(["Buy groceries", "Finish extra lab", "Eat banana"])
    mark_complete_tool.mark_complete(1, "bought")
    mark_complete_tool.mark_complete(2, "finished")
    
    # Example of using the tool with the LLM. The system prompt instructs the LLM to use the tool to solve the problem, 
    # and the user message provides the problem to solve. The LLM will call the tool as needed to create todos and mark them complete, 
    # and then respond with the final solution.
    system_message = """
    You are given a problem to solve, by using your todo tools to plan a list of steps, then carrying out each step in turn.
    Now use the todo list tools, create a plan, carry out the steps, and reply with the solution.
    If any quantity isn't provided in the question, then include a step to come up with a reasonable estimate.
    Provide your solution in Rich console markup without code blocks.
    Do not ask the user questions or clarification; respond only with the answer after using your tools.
    """
    user_message = """"
    A train leaves Boston at 2:00 pm traveling 60 mph.
    Another train leaves New York at 3:00 pm traveling 80 mph toward Boston.
    When do they meet?
    """
    messages = [{"role": "system", "content": system_message}, {"role": "user", "content": user_message}]
    mark_complete_tool.loop(messages)
    