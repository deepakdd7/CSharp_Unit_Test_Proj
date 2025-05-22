# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import os
import json
from openai import AzureOpenAI

endpoint = "<URL>"
model_name = "gpt-4o"
deployment = "gpt-4o"

subscription_key = "<KEY>"
api_version = "2025-01-01-preview"

client = AzureOpenAI(
    api_key=subscription_key,
    api_version=api_version,
    azure_endpoint=endpoint
    )

def find_controller_file(start_dir="."):
    for root, _, files in os.walk(start_dir):
        for file in files:
            if file.endswith("Controller.cs"):
                return os.path.join(root, file)
    return None

def read_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def print_directory_tree(root_dir, prefix=""):
    sub_dir = sorted(os.listdir(root_dir))
    sub_dir_count = len(sub_dir)
    
    for index, entry in enumerate(sub_dir):
        path = os.path.join(root_dir, entry)    
        connector = "|___" if index == sub_dir_count - 1 else "|---"
        print(prefix + connector + entry)
    
        if os.path.isdir(path):
            extension = "   " if index == sub_dir_count - 1 else "|   "
            print_directory_tree(path, prefix + extension)
        
        
def send_to_openai(file_content):
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful C# coding assistant. Please perform following\n\nProvide interclass dependencies with relevant relative path and filenames for below source code based on linux , ignore external dependencies.\n\nAppend all path with 'Session_B2B'. Provide response in below format with no explanation.\n Internal Dependencies: {[Path1,Path2]}"},
            {"role": "user", "content": f"Here is a C# controller:\n\n{file_content}\n\n"}
        ],
        temperature=0.2,
        top_p=0.2,
        model=deployment
    )
    return response.choices[0].message.content

def send_final_context_to_openai(controller_file, dep_content):
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful C# coding assistant. Generate unit test case for the code mentioned under main class in file {controller_file}, using dependencies in file {dep_content} mentioned under depend classes. Ensure output is syntactically correct."},
            {"role": "user", "content": f"Here is a C# controller:\n\n{file_content}\n\n"}
        ],
        temperature=0.2,
        top_p=0.2,
        model=deployment
    )
    return response.choices[0].message.content


# Main execution
if __name__ == "__main__":
    final_context = ""
    controller_path = find_controller_file()
    if not controller_path:
        print("No Controller.cs file found.")
    else:
        print(f"Found file: {controller_path}")
        content = read_file(controller_path)
        dep_files = send_to_openai(content)
        dep_files = dep_files.split(":")[1].strip()
        dep_files = dep_files.strip('{}[]')
        dep_files = [item.strip() for item in dep_files.split(",")]
        
        print("\n--- Explanation from OpenAI ---\n")
        
        root_dir = os.getcwd()
        print_directory_tree(root_dir)
        for file in dep_files:
            try:
                with open(file, 'r') as f:
                    file_content = f.read()
                    final_context += "".join(file_content)
            except:
                pass
        final_resonse = send_final_context_to_openai(controller_path, final_context)
        print(final_resonse)

