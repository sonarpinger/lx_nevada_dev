import database as db
import argparse

def obtain_session():
  try:
    session = db.get_session()
  except Exception as e:
    logger.error(f"Error obtaining session: {e}")
    raise
  return next(session)

if __name__ == "__main__":
    session = obtain_session()
    username = input("Enter username: ")
    user = db.get_user_by_username(session, username)
    user_dict = db.dump_user_to_dict(session, user)
    print(user_dict)
    