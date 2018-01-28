class DuplicateUsernameError(Exception):
    """
    Username is already taken
    """


class InvalidUsernameException(Exception):
    """
    Given username was not found in the DB
    """
