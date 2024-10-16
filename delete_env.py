#/!usr/bin/env python3

import os
import sys
import argparse
import database as db
from pve_tasks import PVECluster
import apache_tasks as apache
import ansible_tasks as ansible

parser = argparse.ArgumentParser(description="Create a class")
parser.add_argument('--env', type=str, help="environment to delete", required=True)
parser.add_argument('--node', type=str, help="node to delete vm from", required=True)

pve = PVECluster()

def obtain_session():
  try:
    session = db.get_session()
  except Exception as e:
    logger.error(f"Error obtaining session: {e}")
    raise
  return next(session)

def main(args):
  print(f"Deleting VM: {args.env} on node {args.node}")
  pve.select_node(args.node)
  input("Press Enter to continue...")

  session = obtain_session()

  db.delete_env(session, args.env)
  pve.delete_lxc_env(args.env)
  ansible.remove_host_from_inventory(args.env)
  apache.remove_apache_conf(args.env)
  print(f"Deleted VM: {args.env}")

  session.commit()
  session.close()
  print("Done! Please restart the apache2 service and the LX webserver to see the changes.")


    
if __name__ == "__main__":
  args = parser.parse_args()
  main(args)
