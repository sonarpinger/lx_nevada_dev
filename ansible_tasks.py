import os

ANSIBLE_INVENTORY_FILE = "/srv/lx/ansible/hosts"

def read_inventory_file():
    """Reads the Ansible inventory file and returns its content."""
    file_path = ANSIBLE_INVENTORY_FILE
    if not os.path.exists(file_path):
        return ""
    
    with open(file_path, 'r') as file:
        return file.read()

def add_host_to_inventory(inventory_content, hostname, ip_address):
    """Adds a hostname and IP address to the inventory content under a specific group."""
    inventory_lines = inventory_content.splitlines()
    for line in inventory_lines:
        if line.startswith(hostname):
            print(f"Host {hostname} already exists in the inventory.... exiting")
            return inventory_content
    inventory_lines.append(f"{hostname} ansible_host={ip_address}")
    
    return "\n".join(inventory_lines)

def write_inventory_file(content):
    """Writes the updated content back to the inventory file."""
    file_path = ANSIBLE_INVENTORY_FILE
    with open(file_path, 'w') as file:
        file.write(content)

def update_inventory(hostname, ip_address):
    """Main function to update the Ansible inventory."""
    file_path = ANSIBLE_INVENTORY_FILE
    inventory_content = read_inventory_file()
    updated_content = add_host_to_inventory(inventory_content, hostname, ip_address)
    write_inventory_file(updated_content)

def remove_host_from_inventory(hostname):
    """Removes a host from the inventory file."""
    inventory_content = read_inventory_file()
    inventory_lines = inventory_content.splitlines()
    updated_lines = []
    for line in inventory_lines:
        if not line.startswith(hostname):
            updated_lines.append(line)
    updated_content = "\n".join(updated_lines)
    write_inventory_file(updated_content)

def update_line_in_inventory(hostname, ip_address):
    """Updates the IP address of a host in the inventory file."""
    inventory_content = read_inventory_file()
    inventory_lines = inventory_content.splitlines()
    updated_lines = []
    for line in inventory_lines:
        if line.startswith(hostname):
            updated_lines.append(f"{hostname} ansible_host={ip_address}")
        else:
            updated_lines.append(line)
    updated_content = "\n".join(updated_lines)
    write_inventory_file(updated_content)

# Example usage:
if __name__ == "__main__":
    update_inventory("webserver1", "192.168.1.0")
    update_inventory("webserver2", "192.168.2.0")
