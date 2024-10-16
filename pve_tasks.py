import sys
import subprocess
from subprocess import PIPE
import json
from config import settings
from time import sleep
from typing import List
from proxmoxer import ProxmoxAPI
from proxmoxer.core import ResourceException, AuthenticationError
import urllib3
import paramiko

urllib3.disable_warnings()

def create_proxmox_connection():
  prox = ProxmoxAPI(settings.PVE_HOST, user=settings.PVE_USER, password=settings.PVE_PASSWORD.get_secret_value(), verify_ssl=False)
  return prox

proxmox = create_proxmox_connection()

def proxmox_api_call(api_function):
    global proxmox
    try:
        # print(api_function)
        result = api_function()
    except AuthenticationError:
        print("Reconnecting to Proxmox")
        proxmox = create_proxmox_connection()
        result = api_function()
    return result

class SSHConnection:
  def __init__(self, host, user, password):
    self.host = host
    self.user = user
    self.password = password
    self.client = paramiko.SSHClient()
    self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    self.client.connect(self.host, username=self.user, password=self.password)

  def execute_command(self, command):
    stdin, stdout, stderr = self.client.exec_command(command)
    return stdout.channel.recv_exit_status(), stdout.read()

  def close(self):
    self.client.close()

  def __del__(self):
    self.client.close()

class PVECluster:
  def __init__(self):
    self.cluster = {
      "pve1": "IP",
      "pve2": "IP",
      "pve3": "IP",
      "pve4": "IP",
      "pve5": "IP",
      "pve6": "IP",
      "pve7": "IP",
      "pve8": "IP",
      "pve9": "IP",
      "pve10": "IP"
    }
    self.selected_node_ip = None
    self.selected_node = None
    self.ssh_connection = None
    self.pve = create_proxmox_connection()

  def select_node(self, node):
    self.selected_node_ip = self.cluster[node]
    self.selected_node = node
    self.ssh_connection = SSHConnection(self.selected_node_ip, "root", "") #dont need password
    print(f"Selected Node: {self.selected_node}")
    print(f"Connection status: { "Connected" if self.ssh_connection.client.get_transport().is_active() else "Disconnected" }")
    self.test_connection()

  def get_lxc_ip(self, vmid):
    ifs = proxmox_api_call(lambda: self.pve.nodes(self.selected_node).lxc(vmid).interfaces.get())
    for interface in ifs:
      if interface['name'] == 'eth0':
        # inet is optionally returned when the interface is up
        try:
          # return the IP address without CIDR notation
          #print(interface['inet'].split('/')[0])
          return interface['inet'].split('/')[0]
        except KeyError:
          return None
    return None

  def get_envs_on_node(self):
    envs = []
    for vm in proxmox_api_call(lambda: self.pve.nodes(self.selected_node).lxc.get()):
      envs.append(vm['name'])
    return envs

  def get_status(self, vmid):
    try:
      lxc = proxmox_api_call(lambda: self.pve.nodes(self.selected_node).lxc(vmid).status.current.get())
    except Exception as e:
      lxc = None

    if lxc:
        return lxc['status']
    return f"Machine not found on selected node: {self.selected_node}"

  def return_ip_addr(self, vmname):
    rc, output = self.ssh_connection.execute_command(f"/root/get_container_ip.sh {vmname}")
    if rc != 0:
        print(f"Error getting IP for VM: {vmname}")
        sys.exit(1)
    ip = output.decode().strip()
    print(f"IP for {vmname}: {ip}")
    return ip

  def get_vm_ip_addrs_for_user(self, user):
    for env in user.envs:
      rc, output = self.ssh_connection.execute_command(f"/root/get_container_ip.sh {env.vmname}")
      if rc != 0:
        print(f"Error getting IP for VM: {env.vmname}")
        sys.exit(1)
            
      ip = output.decode().strip()
      print(f"IP for {env.vmname}: {ip}")
      env.setIP(ip)
    
  def test_connection(self):
    command = "/root/test_conn.sh ping"
    rc, output = self.ssh_connection.execute_command(command)
    output = output.decode().strip()
    print(f"ping..... {output}")

  def add_users_to_envs(self, user):
    for env in user.envs:
      rc, output = self.ssh_connection.execute_command(f"/root/create_lx_user.sh {env.vmname} {user.username}")
      if rc != 0:
        print(f"Error creating user for VM: {env.vmname}")
        print(output.decode().strip())
        sys.exit(1)

  def create_lxc_clone(self, hostname, template):
    #check if container with hostname exists
    check_command = f"/root/get_container_vmid.sh {hostname}"
    rc, output = self.ssh_connection.execute_command(check_command)
    if rc == 0 and output.decode().strip() != "":
      print(f"Container with hostname {hostname} already exists")
      return output.decode().strip()
    # vmid = self.pve.cluster.nextid.get()
    vmid = proxmox_api_call(lambda: self.pve.cluster.nextid.get())
    command = f"/root/create_lxc_clone.sh {vmid} {hostname} {template}"
    print(command)
    rc, output = self.ssh_connection.execute_command(command)
    if rc != 0:
      print(f"Error creating LXC: {hostname}")
      print(output.decode().strip())
      sys.exit(1)
    return vmid

  def create_lxc_envs(self, env_list):
    for env in env_list:
      vmid = self.create_lxc_clone(env.vmname, env.template)
      env.setVMID(vmid)

  def start_lxc_envs(self, env_list):
    for env in env_list:
      rc, output = self.ssh_connection.execute_command(f"/root/start_container.sh {env.vmname}")
      if rc != 0:
        print(f"Error starting LXC: {env.vmname}")
        print(output)
        sys.exit(1)

  def start_lxc(self, env):
    rc, output = self.ssh_connection.execute_command(f"/root/start_container.sh {env.machine_name}")
    if rc != 0:
      print(f"Error starting LXC: {env.machine_name}")
      print(output)
      sys.exit(1)
    # wait for container to start
    counter: int = 0
    while self.get_status(env.vmid) == 'stopped':
      counter += 1
      sleep(1)
      if counter > 120:
        print(f"Error starting LXC: {env.machine_name}")
        sys.exit(1)
    print(f"Started LXC: {env.machine_name}... waiting for network to come up")
    while self.get_lxc_ip(env.vmid) == None:
      counter += 1
      sleep(1)
      if counter > 120:
        print(f"Error getting IP for: {env.machine_name}")
        sys.exit(1)

  def shutdown_lxc(self, env):
    rc, output = self.ssh_connection.execute_command(f"/root/shutdown_container.sh {env.machine_name}")
    if rc != 0:
      print(f"Error shutting down LXC: {env.machine_name}")
      print(output)
      sys.exit(1)
    # dont need to wait for shutdown
    # counter: int = 0
    # while self.get_status(env.vmid) != 'stopped':
      # counter += 1
      # sleep(1)
      # if counter > 120:
        # print(f"Error shutting down LXC: {env.machine_name}")
        # sys.exit(1)

  def create_start_lxc(self, env_list):
    print("Creating LXC Containers...")
    self.create_lxc_envs(env_list)
    print("Starting LXC Containers...")
    sleep(10)
    self.start_lxc_envs(env_list)
    print("Waiting for LXC Containers to start...")
    sleep(30)

  def delete_lxc_env(self, vmname):
    rc, output = self.ssh_connection.execute_command(f"/root/delete_container.sh {vmname}")
    if rc != 0:
      print(f"Error deleting LXC: {vmname}")
      print(output.decode().strip())
      sys.exit(1)

if __name__ == "__main__":
  class TestEnv():
    def __init__(self, machine_name, vmid):
      self.machine_name = machine_name
      self.vmid = vmid
  test_env = TestEnv("", 201)
  pve = PVECluster()
  pve.select_node("")
  pve.test_connection()
  pve.start_lxc(test_env)
