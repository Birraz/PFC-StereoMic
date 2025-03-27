from threading import Lock

# Dictionary of named locks
shared_locks = {
    "file": Lock(),
    "audio": Lock(),
}

def get_lock(name):
    return shared_locks[name]
