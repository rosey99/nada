# Creating Users

This document describes how to use the `scripts/user/create_users.py` script to create users in the Nada system.

## Overview

The `create_users.py` script allows you to create one or more users either interactively via the terminal or from a JSON file. Users are stored in Redis and hashed for security.

## Prerequisites

- The Nada project must be installed (`pip install -e .`)
- Redis must be running and accessible
- The `REDIS_DATA_HOST`, `REDIS_DATA_PORT`, and `REDIS_DATA_DBNUM` environment variables must be configured

## Usage

### Interactive Mode

Run the script without any arguments to create users interactively:

```bash
cd default/src/nada
python -m nada.scripts.user.create_users
```

The script will prompt you for the following required fields:

| Field | Description |
|---|---|
| `username` | Unique username (required) |
| `display_name` | Display name for the user (required) |
| `email` | Email address (required, must be valid) |
| `full_name` | Full name (optional) |
| `is_active` | Whether the user is active (0 or 1, default: 1) |
| `is_superuser` | Whether the user is a superuser (0 or 1, default: 0) |
| `password` | User password (required, confirmed on entry) |

After entering a user's details, you will be prompted to add another user or quit.

### JSON File Mode

Create a JSON file with user data. Each user object must contain the required fields:

```json
[
  {
    "username": "alice",
    "display_name": "Alice Smith",
    "email": "alice@example.com",
    "full_name": "Alice Smith",
    "is_active": 1,
    "is_superuser": 0,
    "password": "securepassword1"
  },
  {
    "username": "bob",
    "display_name": "Bob Jones",
    "email": "bob@example.com",
    "full_name": "Bob Jones",
    "is_active": 1,
    "is_superuser": 1,
    "password": "securepassword2"
  }
]
```

Then run the script with the `--path` argument:

```bash
python -m nada.scripts.user.create_users --path users.json
```

### Specifying Redis Port

By default, the script uses the Redis port configured in the environment (`REDIS_DATA_PORT`). You can override this with the `--port` argument:

```bash
# For local development (default Redis port)
python -m nada.scripts.user.create_users --port 6379

# For Docker Compose setup (Redis port 6389)
python -m nada.scripts.user.create_users --port 6389
```

## Command-Line Arguments

| Argument | Description |
|---|---|
| `--port` | Override the Redis port (default: value of `REDIS_DATA_PORT`) |
| `--path` | Path to a JSON file containing user data |

## Notes

- If a user with the same username already exists, the script will overwrite the existing user and log a warning.
- Passwords are hashed using bcrypt before being stored in Redis.
- The `is_active` and `is_superuser` fields accept `0` or `1` as integer values.
- The `email` field must be a valid email address format.
