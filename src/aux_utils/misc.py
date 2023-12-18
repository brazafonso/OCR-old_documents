
def path_to_id(path: str):
    """Convert a path to an id, geting the last 3 parts of the path and joining them with underscores"""
    return '_'.join(path.split('/')[-3:])