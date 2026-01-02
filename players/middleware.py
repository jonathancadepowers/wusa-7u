from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import resolve
from django.shortcuts import render
from .models import DivisionValidationRegistry, ValidationCode, GeneralSetting
import logging

logger = logging.getLogger(__name__)


class ValidationMiddleware:
    """
    Middleware to enforce validation logic based on DivisionValidationRegistry configuration.

    This middleware:
    1. Runs "validations to run on page load" before GET requests are processed
    2. Runs "validation code triggers" after POST/PUT/PATCH/DELETE requests are processed

    All validation lookups are done in real-time (no caching) to ensure current configuration is used.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get the current URL path
        path = request.path

        # Skip validation for admin, static, and media URLs
        if path.startswith('/admin/') or path.startswith('/static/') or path.startswith('/media/'):
            return self.get_response(request)

        # Skip validation for the division_validation_registry page itself to avoid circular dependencies
        if path == '/division_validation_registry/':
            return self.get_response(request)

        # === BEFORE REQUEST: Run "validations to run on page load" for GET requests ===
        if request.method == 'GET':
            validation_error = self._run_page_load_validations(path)
            if validation_error:
                # Block the page from loading and show error message
                return self._render_validation_error(request, validation_error)

        # Process the request
        response = self.get_response(request)

        # === AFTER REQUEST: Run "validation code triggers" for CRUD operations ===
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # Only run triggers if the response was successful (2xx status code)
            if 200 <= response.status_code < 300:
                self._run_validation_triggers(path, request)

        return response

    def _run_page_load_validations(self, path):
        """
        Run validations that must pass before the page can load.

        Returns: Error message string if validation fails, None if all validations pass
        """
        from django.db import connection

        try:
            # Look up validation registry for this page (real-time, no cache)
            registry = DivisionValidationRegistry.objects.filter(page=path).first()

            if not registry:
                # No validations configured for this page
                return None

            # Get the list of validations to run on page load
            validations_to_run = registry.validations_to_run_on_page_load or []

            if not validations_to_run:
                # No validations configured
                return None

            # Fetch all validation codes in a single query to reduce DB hits
            validation_codes = ValidationCode.objects.filter(code__in=validations_to_run).in_bulk(field_name='code')

            # Run each validation
            for validation_code in validations_to_run:
                validation = validation_codes.get(validation_code)

                if not validation:
                    logger.warning(f"Validation code '{validation_code}' not found in database")
                    continue

                # Check if validation value is True (validation passed)
                # (ValidationCode.value is now a BooleanField)
                validation_passed = validation.value

                if not validation_passed:
                    # Validation failed - return the error message
                    error_message = validation.error_message or f"Validation '{validation_code}' failed"
                    logger.info(f"Page load validation failed for {path}: {validation_code}")
                    return error_message

            # All validations passed
            return None

        except Exception as e:
            logger.error(f"Error running page load validations for {path}: {str(e)}")
            # Close connection on error to prevent connection leaks
            try:
                connection.close()
            except:
                pass
            return None  # Don't block page on middleware errors

    def _run_validation_triggers(self, path, request):
        """
        Run validation triggers after CRUD operations.

        These validations call Python validation functions which update the validation_codes table.
        """
        from django.db import connection

        try:
            # Look up validation registry for this page (real-time, no cache)
            registry = DivisionValidationRegistry.objects.filter(page=path).first()

            if not registry:
                return

            # Get the list of validation code triggers
            validation_triggers = registry.validation_code_triggers or []

            if not validation_triggers:
                return

            # Import views module to access validation functions
            from . import views

            # Run each validation trigger
            for validation_code in validation_triggers:
                # Check if Python validation function exists
                if not hasattr(views, validation_code):
                    logger.warning(f"Validation function '{validation_code}' not found in views")
                    continue

                # Call the Python validation function
                # The function will update the ValidationCode.value field to "true" or "false"
                validation_function = getattr(views, validation_code)
                validation_function()

                logger.info(f"Validation trigger '{validation_code}' executed for {path}")

        except Exception as e:
            logger.error(f"Error running validation triggers for {path}: {str(e)}")
            # Close connection on error to prevent connection leaks
            try:
                connection.close()
            except:
                pass

    def _render_validation_error(self, request, error_message):
        """
        Render an error page when validation fails.
        """
        context = {
            'error_message': error_message,
            'page_url': request.path,
        }

        return HttpResponse(
            f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Validation Error - WUSA 7U</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    body {{
                        background-color: #f8f9fa;
                        padding: 50px 0;
                    }}
                    .error-container {{
                        max-width: 600px;
                        margin: 0 auto;
                    }}
                    .error-icon {{
                        font-size: 4rem;
                        color: #dc3545;
                    }}
                </style>
            </head>
            <body>
                <div class="error-container">
                    <div class="card shadow">
                        <div class="card-body text-center p-5">
                            <div class="error-icon mb-4">⚠️</div>
                            <h2 class="mb-4">Validation Error</h2>
                            <div class="alert alert-danger" role="alert">
                                {error_message}
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """,
            status=403
        )


class MasterPasswordMiddleware:
    """
    Middleware to enforce master password authentication on all pages except exempt ones.

    Exempt pages:
    - public_portal/
    - team_preferences/
    - teams/<team_secret>/ (team detail pages with team secrets, but NOT /teams/ list)
    - player_rankings
    - manager_daughter_rankings/
    - practice_slot_rankings
    - player_rankings/analyze/public/
    """

    # Define exempt URL patterns
    EXEMPT_PATHS = [
        '/public_portal/',
        '/team_preferences/',
        '/player_rankings/',
        '/manager_daughter_rankings/',
        '/practice_slot_rankings/',
        '/player_rankings/analyze/public/',
        '/admin/',
        '/static/',
        '/media/',
    ]

    # API endpoints that need to be exempt
    EXEMPT_API_PATHS = [
        '/api/verify-master-password/',
        '/api/validate-team-secret/',
        '/api/managers-list/',
        '/api/update-manager/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Check if this path is exempt
        if self._is_exempt_path(path):
            return self.get_response(request)

        # Check if user has valid master password cookie
        cookie_password = request.COOKIES.get('master_password')
        db_password = self._get_master_password_from_db()

        # If cookie exists and matches database password, allow access
        if cookie_password and cookie_password == db_password:
            return self.get_response(request)

        # User needs to be challenged - inject password requirement flag
        request.needs_master_password_challenge = True

        return self.get_response(request)

    def _is_exempt_path(self, path):
        """Check if the given path is exempt from master password authentication."""
        # Check standard exempt paths
        for exempt_path in self.EXEMPT_PATHS + self.EXEMPT_API_PATHS:
            if path.startswith(exempt_path):
                return True

        # Special handling: Exempt team detail pages (/teams/<team_secret>/) but not the list (/teams/)
        if path.startswith('/teams/') and path != '/teams/' and len(path.split('/')) >= 3:
            # Path is like /teams/abc123/ or /teams/abc123/toggle-star/
            return True

        return False

    def _get_master_password_from_db(self):
        """Retrieve master password from database."""
        try:
            setting = GeneralSetting.objects.filter(key='master_password').first()
            if setting:
                return setting.value
            else:
                return 'wusarocks'  # Default fallback
        except:
            return 'wusarocks'  # Default fallback on error
