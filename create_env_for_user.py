#/!usr/bin/env python3

import os
import sys
import csv
import yaml
import argparse
import database as db
from pve_tasks import PVECluster
import apache_tasks as apache
import ansible_tasks as ansible

parser = argparse.ArgumentParser(description="Create a class")
parser.add_argument('--template', type=str, help="name of template", required=True)
parser.add_argument('--course', type=str, help="course to create vm for", required=True)
parser.add_argument('--username', type=str, help="username to create vm for", required=True)
parser.add_argument('--node', type=str, help="node to create vm on", required=True)

pve = PVECluster()

def obtain_session():
  try:
    session = db.get_session()
  except Exception as e:
    logger.error(f"Error obtaining session: {e}")
    raise
  return next(session)

class LocalUser():
  def __init__(self, username, course):
    self.username = username
    self.course = course
    self.envs = []

class LocalEnv():
  def __init__(self, vmname, template, node):
    self.vmname = vmname
    self.template = template
    self.node = node
  def setIP(self, ip):
    self.ip = ip
  def setVMID(self, vmid):
    self.vmid = vmid

def main(args):
  print(f"Creating VM for {args.username} in course {args.course} on node {args.node} from template {args.template}")
  pve.select_node(args.node)
  session = obtain_session()
  input("Press Enter to continue...")

  hostname = f"{args.course}-{args.username}"
  local_user = LocalUser(args.username, args.course)
  local_env = LocalEnv(hostname, args.template, args.node)
  local_user.envs.append(local_env)
  pve.create_start_lxc([local_env])
  print(f"Created VM: {hostname} ")
  pve.add_users_to_envs(local_user)
  pve.get_vm_ip_addrs_for_user(local_user)
  db.create_user(session, local_user.username)
  for env in local_user.envs:
    db.create_environment_for_user(session, local_env.vmname, local_user.course, env.vmid, local_user.username)
    db.add_ip_address(session, env.vmname, local_env.ip)
    db.set_env_status(session, env.vmid, "running")
    apache.render_and_write_apache_template(env.vmname, local_user.username, env.ip)
    ansible.update_inventory(env.vmname, env.ip)

  apache.reload_apache()
  session.commit()
  session.close()
  print("Done! Please restart the apache2 service and the LX webserver to see the changes.")
    
if __name__ == "__main__":
  args = parser.parse_args()
  main(args)
