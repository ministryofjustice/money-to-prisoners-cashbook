class MtpUser(object):
    """
    Authenticated user, similar to the Django one.

    The built-in Django `AbstractBaseUser` sadly depends on a few tables and
    cannot be used without a datbase so we had to create a custom one.
    """
    def __init__(self, token):
        self.pk = token
        self.is_active = True

    def save(self, *args, **kwargs):
        pass

    def is_authenticated(self, *args, **kwargs):
        return True


class MtpAnonymousUser(object):
    """
    Anonymous non-authenticated user, similar to the Django one.

    The built-in Django `AnonymousUser` sadly depends on a few tables and
    gives several warnings when used without a database so we had to create a
    custom one.
    """

    def is_authenticated(self, *args, **kwargs):
        return False
