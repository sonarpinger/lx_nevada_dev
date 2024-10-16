import database as db

def obtain_session():
  try:
    session = db.get_session()
  except Exception as e:
    logger.error(f"Error obtaining session: {e}")
    raise
  return next(session)


def print_all_users():
    session = obtain_session()
    users = db.get_all_users(session)
    for user in users:
        print(user.username)
        user = db.get_user_by_username(session, user.username)
        environments = db.query_envs_for_user(session, user)
        for environment in environments:
            print(f"\tEnvironment: {environment.machine_name} IP: {environment.ip_address} Status: {environment.status}")

    #envs = db.query_all_envs(session)
    #for env in envs:
        #print(f"Environment: {env.machine_name} IP: {env.ip_address}")
    
def delete_all_users_and_envs():
    session = obtain_session()
    users = db.get_all_users(session)
    for user in users:
        user = db.get_user_by_username(session, user.username)
        db.delete_user_and_envs(session, user)
    
    envs = db.query_all_envs(session)
    for env in envs:
        session.delete(env)
        session.commit()

if __name__ == "__main__":
    print_all_users()