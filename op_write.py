import os
import re
import sys
import xml.etree.ElementTree as ET

EXCLUDE_NODES = ['clear', 'show']  # Add other elements to this list as needed

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def write_node_def(path, help_text=None, run_command=None, allowed=None):
    with open(os.path.join(path, 'node.def'), 'w') as f:
        if help_text:
            f.write(f"help: {help_text}\n")
        if run_command:
            f.write(f"run: {run_command}\n")
        if allowed:
            f.write(f"allowed: {allowed}\n")

def replace_includes(xml_text):
    include_pattern = re.compile(r'#include\s+<([^>]+)>')

    def include_replacer(match):
        include_file = match.group(1)
        with open(include_file, 'r') as f:
            return f.read()

    return include_pattern.sub(include_replacer, xml_text)

def parse_node(node, parent_path):
    if 'name' in node.attrib:
        node_name = node.attrib['name']
        node_path = os.path.join(parent_path, node_name)
        create_directory(node_path)

        help_text = node.find('properties/help').text if node.find('properties/help') is not None else None
        run_command = node.find('command').text if node.find('command') is not None else None
        allowed = None

        if node_name not in EXCLUDE_NODES:  # Skip creating node.def for elements in EXCLUDE_NODES
            if node.tag == 'tagNode':
                create_directory(os.path.join(node_path, 'node.tag'))
                completion_help_path = node.find('properties/completionHelp/path').text if node.find('properties/completionHelp/path') is not None else ""
                completion_help_list = node.find('properties/completionHelp/list').text if node.find('properties/completionHelp/list') is not None else ""
                completion_help_script = node.find('properties/completionHelp/script').text if node.find('properties/completionHelp/script') is not None else ""

                allowed_parts = []
                if completion_help_list:
                    allowed_parts.append(f'echo "{completion_help_list}"')
                if completion_help_path:
                    allowed_parts.append(f'/bin/cli-shell-api listActiveNodes {completion_help_path} | sed -e "s/\'//g"')
                if completion_help_script:
                    allowed_parts.append(completion_help_script)
                allowed = " && ".join(allowed_parts) + " && echo"

                # Write node.def inside node.tag directory with run and allowed
                write_node_def(os.path.join(node_path, 'node.tag'), help_text, run_command, allowed)
                # Write node.def before node.tag directory with only help
                write_node_def(node_path, help_text)
            else:
                if node.tag == 'leafNode' or run_command:
                    write_node_def(node_path, help_text, run_command)
                else:
                    write_node_def(node_path, help_text)

        if node.find('children') is not None:
            for child in node.find('children'):
                parse_node(child, node_path)
    else:
        if node is not None:
            for child in node:
                parse_node(child, parent_path)

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 op_write.py <path_to_your_xml_file>")
        sys.exit(1)

    xml_file = sys.argv[1]
    with open(xml_file, 'r') as f:
        xml_text = f.read()

    xml_text = replace_includes(xml_text)
    root = ET.fromstring(xml_text)

    base_path = '/opt/vyatta/share/vyatta-op/templates'
    create_directory(base_path)
    parse_node(root, base_path)

if __name__ == "__main__":
    main()
