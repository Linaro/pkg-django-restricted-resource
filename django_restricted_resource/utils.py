def filter_bogus_users(user):
    """
    Check for bogus instances of user (anonymous, disabled, etc) and
    change them to None. This simplifies user comparison and handling.
    If the user is `None' then he's not trusted, period, no need to
    check deeper.
    """
    if user is not None and user.is_authenticated() and user.is_active:
        return user
