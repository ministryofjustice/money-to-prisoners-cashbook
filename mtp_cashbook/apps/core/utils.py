from django.conf import settings


def retrieve_all_pages(api_endpoint):
    """
    Some MTP apis are paginated, this method loads all pages into a single results list
    :param api_endpoint: slumber callable, e.g. `[api_client].cashbook.transactions.locked.get`
    """
    loaded_results = []

    offset = 0
    while True:
        response = api_endpoint(limit=settings.REQUEST_PAGE_SIZE, offset=offset)
        count = response.get('count', 0)
        new_results = response.get('results', [])
        loaded_results += new_results
        if len(loaded_results) >= count:
            break
        offset += settings.REQUEST_PAGE_SIZE

    return loaded_results
