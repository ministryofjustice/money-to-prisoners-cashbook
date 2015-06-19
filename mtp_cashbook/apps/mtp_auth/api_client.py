import slumber

from django.conf import settings
from django.utils.http import urlencode


class FormSerializer(slumber.serialize.JsonSerializer):
    key = "form"
    content_types = ["application/x-www-form-urlencoded", "application/json"]

    def dumps(self, data):
        return urlencode(data)


def get_auth_connection():
    """
    Returns a slumber connection configured so that it can be easily
    used for authentication.
    """
    s = slumber.serialize.Serializer(
        default="form",
        serializers=[
            FormSerializer(),
        ]
    )

    return slumber.API(settings.API_URL, serializer=s)
