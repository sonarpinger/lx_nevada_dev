import os
import sys
import csv
import yaml
import argparse
import database as db
from pve_tasks import PVECluster
import apache_tasks as apache

parser = argparse.ArgumentParser(description="Delete a class")
parser.add_argument('--file', type=str, help="YAML file to parse", required=True)

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

# parsing creates local objects for users and environments
def parse_yml_file(yaml_file, local_envs, local_users, local_course_name):
  with open(yaml_file, 'r') as f:
    try:
      data = yaml.safe_load(f)

      if data['class'] is None:
        print("No Class Provided")
        sys.exit(1)
        
      if(len(data['names']) <= 0):
        print("No User Names Supplied!")
        sys.exit(1)

      # add users to local_users
      for user in data['names']:
        username = user.strip()
        local_users.append(LocalUser(username, data['class']))


      print(f"Each user will be in the class: {data['class']}")
      print(f"Machines will be provisioned on the node: {data['node']}")

      pve.select_node(data['node'])
      local_course_name['name'] = data['class']
      
    except yaml.YAMLError as e:
      print(f"Error: {e}")

def main(args):
  session = obtain_session()

  yaml_file = args.file
  local_envs = []
  local_users = []
  local_course_name = {}
  
  parse_yml_file(yaml_file, local_envs, local_users, local_course_name)
  for user in local_users:
    print(f"User: {user.username} Course: {user.course}")
    for env in user.envs:
      print(f"\tVM: {env.vmname} Template: {env.template} Node: {env.node}")
  input("Press Enter to continue...")
  
  pve.create_start_lxc(local_envs)
    
  for user in local_users:
    db.create_user(session, user.username)
    pve.add_users_to_envs(user)
    pve.get_vm_ip_addrs_for_user(user)
    for env in user.envs:
      db.create_environment_for_user(session, env.vmname, user.course, env.vmid, user.username)
      db.add_ip_address(session, env.vmname, env.ip)
      db.set_env_status(session, env.vmname, "running")
      apache.render_and_write_apache_template(env.vmname, user.username, env.ip)

  session.commit()
  session.close()
  print("Done! Please restart the apache2 service and the LX webserver to see the changes.")
    
if __name__ == "__main__":
  args = parser.parse_args()
  main(args)
