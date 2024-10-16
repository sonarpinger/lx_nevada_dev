from subprocess import PIPE
import subprocess
import jinja2
import sys
import os

APACHE_CONF_DIR = "/etc/apache2/sites-enabled/conf/"

# list of admins which can view any environment
ADMINS = [
    "admin1"
]

def render_apache_template(template, envname, username, ip_addr):
  context = {
    "ip_addr": ip_addr,
    "envname": envname,
    "username": username,
    "admins": ADMINS,
  }
  template = jinja2.Template(open(template).read())
  return template.render(context)

def reload_apache():
  command = "/srv/lx/reload_apache.sh"
  proc = subprocess.run(command, shell=True, stdout=PIPE, stderr=PIPE)
  if proc.returncode != 0:
    print(f"Error reloading apache: {proc.stderr}")
    sys.exit(1)

def render_and_write_apache_template(envname, username, ip_addr):
  template = "apache-template.j2"
  output_file = f"{APACHE_CONF_DIR}/{envname}.conf"
  rendered = render_apache_template(template, envname, username, ip_addr)
  with open(output_file, "w") as f:
    f.write(rendered)
  # reload_apache()

def remove_apache_conf(envname):
  conf_file = f"{APACHE_CONF_DIR}/{envname}.conf"
  if os.path.exists(conf_file):
    os.remove(conf_file)
    # reload_apache()
  else:
    print(f"Error: {conf_file} does not exist")
    sys.exit(1)

def get_env_ip_addr(envname):
  apache_conf_file = f"{APACHE_CONF_DIR}/{envname}.conf"
  if not os.path.exists(apache_conf_file):
    return None
  with open(apache_conf_file, "r") as f:
    for line in f:
      if "ProxyPass" in line:
        return line.split("//")[1].split(":")[0].strip()

def update_apache_conf(envname, username, ip_addr):
  remove_apache_conf(envname)
  render_and_write_apache_template(envname, username, ip_addr)

if __name__ == "__main__":
  # test
  print(get_env_ip_addr(envname))
