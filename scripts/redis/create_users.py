# Create one or more users
import asyncio
import json
import sys

from typing import List, Union
from nada.deps import SessionDep
from nada.models import User
from nada.security import create_user
from nada.settings import settings

import argparse

import logging
logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)


async def create_users(users: Union[List[User], User], port=6379):
    """
    create one or more users
    """
    i = 0
    if not isinstance(users, list):
        users = [users]
    for user in users:
        passw = user.pop("password")
        _ = await create_user(db=SessionDep(db=settings.REDIS_DATA_DBNUM, port=port), user_data=user, password=passw)
        i += 1
    return i

def main():
    """
    Takes a single optional json file path for users to create,
    or drops to a terminal. Optionally an overide port can be specified.
    """

    required_names = {
        "username": "",
        "display_name": "",
        "email": "",
        "full_name": "",
        "is_active": " (0/1)",
        "is_superuser": " (0/1)",
        "password": "",
    }

    parser = argparse.ArgumentParser(
        description=f"Adds one or more users either interactively via a terminal or from a local json file. \n{'\nRequired fields: ' + '\n'.join([name for name in required_names])}",  # Capitalized + period
        epilog="Example: python create_users.py --path users.json --port 6389"
    )
    parser.add_argument("--port", action="store", help="specify redis port, by default 6389 for container and 6379 for local")
    parser.add_argument("--path", action="store", help="specify path to JSON file with users and passwords for loading, see")
    args = parser.parse_args()

    users = []
    if args.path:
        # open a file
        try:
            with open(args.path, 'r') as file:
                _users = file.read()
                _users = json.loads(_users)
                for u in _users:
                    #user = User(**u)
                    users.append(u)
            #return asyncio.run(create_user(users))

        except Exception as e:
            print(str(e))
            sys.exit(str(e))
    else:
        # Do it by hand
        def get_passwords():
            pass1 = input("password: ")
            pass2 = input("again please: ")
            pass1, pass2 = pass1.strip(), pass2.strip()
            if not pass1 == pass2:
                return
            return pass1

        quit = False
        while not quit:
            user = {}
            for name, addl in required_names.items():
                if name != "password":
                    addl_str = addl if addl else ""
                    value = input(f"{name}{addl_str}: ")
                else:
                    count = 0
                    while count < 4:
                        good_pass = get_passwords()
                        if not good_pass:
                            count += 1
                            continue
                        else:
                            count = 0
                            value = good_pass
                            break
                    if count > 2:
                        # out of loop start over
                        break

                user[name] = value
                if value.lower() in {"exit", "quit"}:
                    quit = True
                    break

            users.append(user)
            do_more = input(f"Add another(y/n)? {len(users)} created so far: ")
            do_more = do_more.lower()
            if do_more in ('y' ,'yes'):
                continue
            if do_more in ('n', 'no'):
                break
    if users:
        if args.port:
            port = int(args.port)
            logger.info(f"Overide port: {port}")
        else:
            port = settings.REDIS_DATA_PORT
        return asyncio.run(create_users(users, port=port))
    else:
        print("No users to create")


if __name__ == '__main__':
    main()
