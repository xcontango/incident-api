import aiohttp
import asyncio
import requests
import structlog
from aiohttp import ClientSession, BasicAuth
from django.conf import settings
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response

ROOT_DATA_URL = settings.ROOT_DATA_URL
INCIDENT_TYPES = [
    'denial',
    'intrusion',
    'executable',
    'misuse',
    'unauthorized',
    'probing',
    'other',
]
PRIORITY_LEVELS = ['low', 'medium', 'high', 'critical']
REQUEST_TIMEOUT = 30  # seconds

logger = structlog.getLogger(__name__)


class IncidentViewSet(generics.ListAPIView):
    authentication_classes = [SessionAuthentication]

    def get_queryset(self):
        try:
            results = asyncio.run(get_all())
            identities = results.pop('identities', {})
            return combine_data(identities, results)
        except:
            return {'error': 'Error connecting to source data'}

    def list(self, request):
        data = self.get_queryset()
        return Response(data)


async def get_all():
    """Sets up an async task to fetch all urls."""
    credentials = BasicAuth(settings.API_USER_NAME, password=settings.API_USER_PASS, encoding='utf8')
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0'}
    # Everything will be in results, identified by top level key
    results = {}
    async with ClientSession(auth=credentials, conn_timeout=REQUEST_TIMEOUT, headers=headers) as session:
        # Async tasks for fetching the urls
        tasks = []
        # Identities go into the same dict of results
        url = f'{ROOT_DATA_URL}identities/'
        tasks.append(get_one(url, session, 'identities', results))

        # Incidents match the same url pattern
        for incident_type in INCIDENT_TYPES:
            url = f'{ROOT_DATA_URL}incidents/{incident_type}/'
            tasks.append(get_one(url, session, incident_type, results))

        await asyncio.gather(*tasks)
        logger.info('finished loading', count=len(tasks), results_count=len(results))
    return results


async def get_one(url, session, incident_type, results):
    """Fetch json for one url and put it into results."""
    logger.info('loading', incident_type=incident_type, url=url)
    rsp = await session.request(method="GET", url=url, ssl=False)
    rsp.raise_for_status()
    results[incident_type] = await rsp.json()


def combine_data(identities, incidents):
    """Build the response dict."""
    return_data = {}

    for incident_type, type_data in incidents.items():
        for row in type_data.get('results', []):
            row['type'] = incident_type

            employee_id = row.get('employee_id')
            if not employee_id:
                # Try IP
                ids = [row.get(k) for k in ('source_ip', 'machine_ip', 'internal_ip', 'ip', 'identifier')]
                for id in ids:
                    if id and isinstance(id, str):
                        employee_id = identities.get(id)
                        if employee_id:
                            break
            if not employee_id:
                # Reach for any identifier
                ids = [row.get(k) for k in ('identifier', 'reported_by', 'source_ip', 'machine_ip', 'internal_ip', 'ip')]
                employee_id = next((id for id in ids if id), None)
            if not employee_id:
                # TODO: what's the fallback if all lookups fail? employee_id is None in this case
                logger.error('could not find an identifier for employee', data=row)

            # Initialize the employee entry with all levels of priorities
            if employee_id not in return_data:
                return_data[employee_id] = {}
                for priority in PRIORITY_LEVELS:
                    return_data[employee_id][priority] = {
                        'count': 0, 'incidents': [],
                    }

            # TODO: check if not a known type?
            priority = row.get('priority')
            return_data[employee_id][priority]['count'] += 1
            return_data[employee_id][priority]['incidents'].append(row)

    logger.info('calculated data by employee', count=len(return_data))
    return return_data
