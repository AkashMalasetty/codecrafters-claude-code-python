import argparse
import os
import sys
import json
from openai import OpenAI

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")

def call_api(messages):
    if not API_KEY:
            raise RuntimeError("OPENROUTER_API_KEY is not set")
    
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    chat = client.chat.completions.create(
        model="anthropic/claude-haiku-4.5",
        messages=messages,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "Read",
                    "description": "Read and return the contents of a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "The path to the file to read"
                            }
                        },
                        "required": ["file_path"]
                    }   
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Write",
                    "description": "Write content to a file",
                    "parameters": {
                        "type": "object",
                        "required": ["file_path", "content"],
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "The path of the file to write to"
                            },
                            "content": {
                                "type": "string",
                                "description": "The content to write to the file"
                            }
                        }
                    }
                }
            }
        ]
    )

    return chat

def execute_tool(tool_call):
    if tool_call.function.name == "Read":
        arguments = json.loads(tool_call.function.arguments)
        with open(arguments["file_path"], "r") as f:
            file_contents = f.read()
            return file_contents

    if tool_call.function.name == "Write":
            arguments = json.loads(tool_call.function.arguments)
            with open("../"+arguments["file_path"], "r") as f:
                file_response = f.write(arguments["content"])
                return file_response

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    messages = [{"role": "user", "content": args.p}]

    while True:
        response = call_api(messages)
        messages.append(response.choices[0].message)

        if(response.choices[0].message.tool_calls is None or len(response.choices[0].message.tool_calls) == 0):
            print(response.choices[0].message.content)
            return

        for tool_call in response.choices[0].message.tool_calls:
            result = execute_tool(tool_call)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })


if __name__ == "__main__":
    main()
