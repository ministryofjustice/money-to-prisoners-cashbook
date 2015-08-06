from moj_auth.models import MojUser


class MtpUser(MojUser):
    """
    MTP specialisation of the MojUser OAuth user
    """

    @property
    def prison(self):
        try:
            return self.user_data.get('prisons', [])[0]
        except IndexError:
            pass
        return None
