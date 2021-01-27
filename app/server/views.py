from django.http import response
import requests
import structlog
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
            session = requests.Session()
            credentials = (settings.API_USER_NAME, settings.API_USER_PASS)
            session.auth = credentials
            session.timeout = REQUEST_TIMEOUT
            identities = get_identities(session)
            incidents = get_incidents(session)
            return combine_data(identities, incidents)
        except:
            return {'error': 'Error connecting to source data'}

    def list(self, request):
        data = self.get_queryset()
        return Response(data)


def get_identities(session):
    """Call the backend to get identities."""
    return_data = {}
    url = f'{ROOT_DATA_URL}identities/'
    logger.info('loading identities', url=url)

    rsp = session.get(url)
    logger.info('api responded', status_code=rsp.status_code)
    if rsp.status_code == 200:
        source = rsp.json()
        logger.info('received identities', count=len(source))
        return_data = source

    return return_data


def get_incidents(session):
    """Call the backend to get all types of incidents."""
    return_data = {}

    for incident_type in INCIDENT_TYPES:
        url = f'{ROOT_DATA_URL}incidents/{incident_type}/'
        logger.info('loading incidents', incident_type=incident_type, url=url)

        rsp = session.get(url)
        logger.info('api responded', incident_type=incident_type, status_code=rsp.status_code)
        if rsp.status_code == 200:
            source = rsp.json()
            logger.info(
                'received incidents',
                incident_type=incident_type,
                count=len(source.get('results') or []),
            )
            return_data[incident_type] = source

    return return_data


def combine_data(identities, incidents):
    return_data = {}

    for incident_type, type_data in incidents.items():
        for row in type_data.get('results', []):
            employee_id = row.get('employee_id')
            if not employee_id:
                # Try IP
                ids = [row.get(k) for k in ('source_ip', 'machine_ip', 'ip', 'identifier')]
                for id in ids:
                    if id and isinstance(id, str):
                        employee_id = identities.get(id)
                        if employee_id:
                            break
            if not employee_id:
                # Try identifier
                employee_id = row.get('identifier')
            # TODO: what's the fallback if all lookups fail? employee_id is None in this case

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

    return return_data
