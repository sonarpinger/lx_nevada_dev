import database as db
from pve_tasks import PVECluster
import apache_tasks as apache
import ansible_tasks as ansible
import sys

def obtain_session():
  try:
    session = db.get_session()
  except Exception as e:
    logger.error(f"Error obtaining session: {e}")
    raise
  return next(session)

# if comes across a stopped environment, it will start the environment temporarily, check/fix its ip, and then stop it again

def main():
  pve = PVECluster()
  pve_list = []
  session = obtain_session()
  for node in pve_list:
    # connect to the node
    pve.select_node(node)
    #get the list of environments on the node
    env_list = pve.get_envs_on_node()

    for env_name in env_list:

      environment = db.get_environment_by_machine_name(session, env_name)
      if environment is None:
        continue

      if environment.status == "stopped":
        print("")
        print(f"{environment.machine_name} status: stopped")
        print(f"Starting {environment.machine_name}")
        pve.start_lxc(environment)

      pve_ip = pve.get_lxc_ip(environment.vmid)
      db_ip = environment.ip_address
      apache_ip = apache.get_env_ip_addr(env_name)

      if pve_ip is None or pve_ip == "":
        print(f"IP not found for {environment.machine_name}")
        sys.exit(1)

      if pve_ip != db_ip or pve_ip != apache_ip:
        print(f"IP mismatch for {environment.machine_name}. PVE: {pve_ip} DB: {db_ip} Apache: {apache_ip}")
        username = environment.users.username
        print(f"Updating IP for {username}'s env: {environment.machine_name} to {pve_ip}")

        db.add_ip_address(session, environment.machine_name, pve_ip)
        apache.update_apache_conf(env_name, username, pve_ip)
        ansible.update_line_in_inventory(environment.machine_name, pve_ip)
      else :
        print(f"{env_name}:: {pve_ip}: GOOD")

      if environment.status == "stopped":
        print(f"Re-stopping {environment.machine_name}")
        pve.shutdown_lxc(environment)
        print("")

if __name__ == "__main__":
  main()
