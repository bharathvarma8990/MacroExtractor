debug_support = 'support.txt'
temp_path = 'temp.txt'
output_path = 'output.txt'
# Specify the folder name or path
folder_name = "Output"

import re
import csv
import os
import shutil
from collections import OrderedDict

def remove_multiline_comments(content):
    comment_pattern = re.compile(r'/\*.*?\*/', re.DOTALL)
    return comment_pattern.sub('', content)

def clean_special_characters(text):
    # Remove non-printable characters (excluding common punctuation and whitespace)
    cleaned_text = re.sub(r'[^\x20-\x7E]', '', text)
    return cleaned_text
    
def extract_macros(content):
    content = remove_multiline_comments(content)

    # Regex to capture both function-like and non-function-like macros
    macro_pattern = re.compile(
        r'#define\s+(\w+)\s*(\([^\)]*\))?\s*(.*)',  # Capture macro definitions, including continuation lines
        re.MULTILINE
    )

    temp_macros = OrderedDict()  # Temporary OrderedDict to store macros
    current_macro = None
    current_body = []
    current_params = ''

    for line in content.splitlines():
        line = line.strip()
        match = macro_pattern.match(line)

        if match:
            if current_macro:
                # Finalize the previous macro
                full_macro = f"{current_macro}{current_params}"
                temp_macros[full_macro] = clean_special_characters(' '.join(current_body).strip())
                current_body = []

            # Start a new macro
            current_macro = match.group(1)
            current_params = match.group(2) if match.group(2) else ''
            body = match.group(3).strip()

            current_body.append(body)

            if not body.endswith("\\"):
                full_macro = f"{current_macro}{current_params}"
                temp_macros[full_macro] = clean_special_characters(' '.join(current_body).strip())
                current_macro = None
                current_body = []
                current_params = ''

        elif current_macro:
            current_body.append(line)

            if not line.endswith("\\"):
                full_macro = f"{current_macro}{current_params}"
                temp_macros[full_macro] = clean_special_characters(' '.join(current_body).strip())
                current_macro = None
                current_body = []
                current_params = ''

    if current_macro:
        full_macro = f"{current_macro}{current_params}"
        temp_macros[full_macro] = clean_special_characters(' '.join(current_body).strip())

    # Finalize formatting and ordering
    macros = OrderedDict()
    for key in temp_macros:
        value = temp_macros[key]
        # Remove standalone backslashes and unwanted escape sequences
        value = re.sub(r'\\.', '', value)
        # Remove extra spaces within the macro body
        value = re.sub(r'\s+', ' ', value).strip()

        # Ensure correct spacing for function-like macros
        if '(' in key:
            # Remove space before and after parentheses
            new_key = re.sub(r'\s*\(\s*', '(', key)
            new_key = re.sub(r'\s*\)\s*', ')', new_key)
            # Add space before '(' for function-like macros
            new_key = re.sub(r'(\w+)\(', r'\1 (', new_key)
            macros[new_key] = value
        else:
            macros[key] = value

    return macros

def extract_nested_parentheses(text):
    stack = []
    results = []
    start_index = None

    for index, char in enumerate(text):
        if char == '(':
            if not stack:
                start_index = index
            stack.append(char)
        elif char == ')':
            stack.pop()
            if not stack:
                results.append(text[start_index:index + 1])

    return results
    
def remove_matching_content(original_string, pattern):
    """
    Removes content from the original_string that matches the given pattern.

    :param original_string: The string from which content will be removed.
    :param pattern: The regular expression pattern to match and remove.
    :return: A new string with the matched content removed.
    """
    # Compile the regular expression pattern
    modified_string = original_string.replace(pattern, '')
    return modified_string
    
def process_line(line):
    # Regex pattern for computation macros with multiple parentheses
    computation_pattern = re.compile(r'^(\w+)\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)\s*(.*)$')
    simple_pattern = re.compile(r'^(\w+)\s+(.*)$')

    # Try to match with computation pattern first
    match = computation_pattern.match(line)
    if match:
        macro_id = match.group(1)  # Macro name
        parameters = match.group(2)  # Parameters inside parentheses
        value = match.group(3)  # Rest of the line as the value
        
        # Handle case where the value might be empty
        if not value.strip():
            # Search from the end of the line backwards to find content between the last ')' and the last '('
            end_pos = line.rfind(')')
            start_pos = line.rfind('(', 0, end_pos)
            if end_pos != -1 and start_pos != -1:
                value = line[end_pos + 1:].strip()
        
        # Combine parameters with macro_id
        full_id = f"{macro_id}({parameters})"
        if(value == ''):
            match2 = extract_nested_parentheses(line)
            if(match2):
                value = match2[0]
                full_id = remove_matching_content(str(full_id),str(match2[0]))
                
        return (full_id, value.strip() if value.strip() else None)
    
    # Try to match with simple pattern if computation pattern does not match
    match_simple = simple_pattern.match(line)
 
    if match_simple:
        macro_id = match_simple.group(1)  # Macro name
        value = match_simple.group(2)  # Rest of the line as the value
        
        # Special case: Handle empty value and no parentheses
        if not value.strip() and '(' not in line:
            return (macro_id, None)  # Empty value and no parentheses
        
        return (macro_id, value.strip())

    return (line,None)

def process_file(filename):
    results = []
    debug_support = []  # List to save lines with empty values and no parentheses

    with open(filename, 'r', encoding='utf-8') as file:  # Ensure correct encoding
        for line in file:
            line = line.strip()
            result = process_line(line)
            #print(result)
            if result:
                macro_id, value = result
                if value is None and '(' not in macro_id:
                    debug_support.append((macro_id, value))
                else:
                    results.append(result)
    
    # Write debug support information to file
    if debug_support:
        with open('debug_support.txt', 'w', encoding='utf-8') as debug_file:
            for macro_id, value in debug_support:
                debug_file.write(f"id: {macro_id}, value: {value}\n")
    
    return results

    
def main():
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    else:
        shutil.rmtree(folder_name)
        os.makedirs(folder_name)

            
    with open('input.txt', 'r', encoding='utf-8') as inputfile: 
        for line in inputfile:
            line = line.strip()
            with open(line, 'r', encoding='utf-8') as file:  # Ensure correct encoding
                content = file.read()
        
            macros = extract_macros(content)
            
            # Change the current working directory
            os.chdir(folder_name)
    
            with open(temp_path,'w',encoding='utf-8') as file:
                for name, details in macros.items():
                # Ensure a space or tab between the macro name and its value
                    file.write(f"{name} {details}\n")
                    
            results = process_file(temp_path)
            
            with open(output_path,'w',encoding='utf-8') as file:
                for macro_id, value in results:
                    file.write(f"{macro_id}->{value}\n")
            
            os.remove(output_path)
            os.remove(temp_path) 
            
            if os.path.exists('output.csv'):
                os.remove('output.csv')
                with open('output.csv','w',newline='',encoding='utf-8') as csvfile:
                    writer =csv.writer(csvfile)
                    writer.writerow(['Macro Name','Macro Definition','Defined File Name'])
            else:
                with open('output.csv','w',newline='',encoding='utf-8') as csvfile:
                    writer =csv.writer(csvfile)
                    writer.writerow(['macro_id','Value','defined file'])
                    
            with open('output.csv','a',newline='',encoding='utf-8') as csvfile2:
                writer2 =csv.writer(csvfile2)
                
                for macro_id,value in results:
                        writer2.writerow([macro_id,value,line])

if __name__ == '__main__':
    main()
