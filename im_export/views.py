import traceback

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from tablib import Dataset

from insuree.apps import InsureeConfig
from .resources import InsureeResource


def check_user_rights(rights):
    class UserWithRights(IsAuthenticated):
        def has_permission(self, request, view):
            return super().has_permission(request, view) and request.user.has_perms(rights)

    return UserWithRights


@api_view(["POST"])
@permission_classes([check_user_rights(InsureeConfig.gql_mutation_create_insurees_perms, )])
def import_insurees(request):
    import_file = request.FILES.get('file', None)

    # todo standarize messages
    if not import_file:
        return Response({'success': False, 'message': 'No import file provided'})

    # todo check regions of current user to forbid adding insurees to non assigned users
    resource = InsureeResource(request.user)

    try:
        data_set = resource.validate_and_sort_dataset(
            Dataset(headers=InsureeResource.insuree_headers).load(import_file.read().decode()))
    except Exception as e:
        # todo for debug, log properly
        traceback.print_exc()
        return Response({'success': False, 'message': 'Failed to parse import file', 'details': str(e)})

    if data_set:
        data_set = data_set.sort('head_insuree_number')
        result = resource.import_data(data_set, dry_run=True)  # Test the data import

        if not result.has_errors():
            resource.import_data(data_set, dry_run=False)  # Actually import
            return Response({'success': True})
        else:
            # todo add proper error reporting, add errors from rows
            return Response({'success': False, 'message': 'Import file contains errors',
                             'details': [str(error.error) for error in result.base_errors]})
    else:
        return Response({'success': False, 'message': 'No rows to import'})


@api_view(["GET"])
@permission_classes([check_user_rights(InsureeConfig.gql_query_insurees_perms, )])
def export_insurees(request):
    # TODO add location based filtering
    return Response(InsureeResource(request.user).export().dict)
