from rest_framework.permissions import DjangoModelPermissions


class EmployeePermissions(DjangoModelPermissions):
    """Same roles as the website. DRF's default ignores 'view' permission on GET, so add it."""
    perms_map = {
        **DjangoModelPermissions.perms_map,
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
    }