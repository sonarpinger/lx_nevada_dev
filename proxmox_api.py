#!/usr/bin/env python3

import json
from time import sleep
from typing import List
from proxmoxer import ProxmoxAPI
from proxmoxer.core import ResourceException, AuthenticationError
from config import settings
import urllib3
import database as db

urllib3.disable_warnings()

# FORMAT
#{
# 	NAME : {
#			status: STATUS,
#			vmid: VMID,
#           type: TYPE
#		},
#}


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

envs_dict = {}

def obj_dict(obj):
    return obj.__dict__

def get_lxc_interfaces(selected_node, vmid):
    ifs = proxmox_api_call(proxmox.nodes(selected_node).lxc(vmid).interfaces.get())
    print(ifs)
    return ifs

def get_machine_node(vmid):
    nodes = proxmox_api_call(lambda: proxmox.nodes.get())
    if not nodes:
        return "No nodes found"
    for pve_node in nodes:
        try:
            vm = proxmox_api_call(lambda: proxmox.nodes(pve_node['node']).qemu(vmid).status.current.get())
        except Exception as e:
            vm = None
        try:
            lxc = proxmox_api_call(lambda: proxmox.nodes(pve_node['node']).lxc(vmid).status.current.get())
        except Exception as e:
            lxc = None

        if not vm and not lxc:
            continue
        else:
            return pve_node['node']
    return "Machine not found"

def get_status (vmid):
    nodes = proxmox_api_call(lambda: proxmox.nodes.get())
    if not nodes:
        return "No nodes found"
    for pve_node in nodes:
        try:
            lxc = proxmox_api_call(lambda: proxmox.nodes(pve_node['node']).lxc(vmid).status.current.get())
        except Exception as e:
            lxc = None

        if lxc:
            return lxc['status']
    return "Machine not found"

def start (vmid, session):
    nodes = proxmox_api_call(lambda: proxmox.nodes.get())
    if not nodes:
        return "No nodes found"
    pve_node = get_machine_node(vmid)
    if pve_node == "Machine not found":
        return pve_node
    try:
        lxc = proxmox_api_call(lambda: proxmox.nodes(pve_node).lxc(vmid).status.start.post())
    except Exception as e:
        lxc = None
    sleep(5)
    db.set_env_status(session, vmid, "running")
    return get_status(vmid)

def shutdown (vmid, session):
    nodes = proxmox_api_call(lambda: proxmox.nodes.get())
    if not nodes:
        return "No nodes found"
    pve_node = get_machine_node(vmid)
    if pve_node == "Machine not found":
        return pve_node
    try:
        lxc = proxmox_api_call(lambda: proxmox.nodes(pve_node).lxc(vmid).status.shutdown.post())
    except Exception as e:
        lxc = None
    sleep(5)
    db.set_env_status(session, vmid, "stopped")
    return get_status(vmid)

def refresh_status_for_user(user, session):
    environments = db.query_envs_for_user(session, user)
    for environment in environments:
        print(f"Refreshing status for {environment.machine_name}")
        status = get_status(environment.vmid)
        db.set_env_status(session, environment.vmid, status)

if __name__ == "__main__":
    # print(get_status(100))
    # print(start(100))
    # print(get_status(100))
    # print(shutdown(100))
    # print(get_status(100))
    # update_envs_list()
    update_envs_list()
