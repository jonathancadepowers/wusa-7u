from django.http import HttpResponse, HttpResponseRedirect
from django.urls import resolve
from django.shortcuts import render
from .models import DivisionValidationRegistry, ValidationCode
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

            # Run each validation
            for validation_code in validations_to_run:
                # Fetch validation from database (real-time, no cache)
                validation = ValidationCode.objects.filter(code=validation_code).first()

                if not validation:
                    logger.warning(f"Validation code '{validation_code}' not found in database")
                    continue

                # Execute the validation logic
                validation_passed = self._execute_validation(validation.value)

                if not validation_passed:
                    # Validation failed - return the error message
                    error_message = validation.error_message or f"Validation '{validation_code}' failed"
                    logger.info(f"Page load validation failed for {path}: {validation_code}")
                    return error_message

            # All validations passed
            return None

        except Exception as e:
            logger.error(f"Error running page load validations for {path}: {str(e)}")
            return None  # Don't block page on middleware errors

    def _run_validation_triggers(self, path, request):
        """
        Run validation triggers after CRUD operations.

        These validations are re-evaluated and the validation_codes table is updated.
        """
        try:
            # Look up validation registry for this page (real-time, no cache)
            registry = DivisionValidationRegistry.objects.filter(page=path).first()

            if not registry:
                return

            # Get the list of validation code triggers
            validation_triggers = registry.validation_code_triggers or []

            if not validation_triggers:
                return

            # Run each validation trigger
            for validation_code in validation_triggers:
                # Fetch validation from database (real-time, no cache)
                validation = ValidationCode.objects.filter(code=validation_code).first()

                if not validation:
                    logger.warning(f"Validation code '{validation_code}' not found in database")
                    continue

                # Execute the validation logic
                validation_result = self._execute_validation(validation.value)

                # Update the validation value in the database
                validation.value = str(validation_result).lower()
                validation.save()

                logger.info(f"Validation trigger '{validation_code}' executed for {path}: {validation_result}")

        except Exception as e:
            logger.error(f"Error running validation triggers for {path}: {str(e)}")

    def _execute_validation(self, validation_code):
        """
        Execute validation logic.

        The validation_code is expected to be a Python expression that evaluates to True/False.
        For example: "Player.objects.count() > 0"

        Returns: Boolean result of the validation
        """
        try:
            # Import models that might be used in validations
            from .models import Player, Team, Manager, Draft, DraftPick, GeneralSetting

            # Create a safe context for evaluation
            context = {
                'Player': Player,
                'Team': Team,
                'Manager': Manager,
                'Draft': Draft,
                'DraftPick': DraftPick,
                'GeneralSetting': GeneralSetting,
            }

            # Evaluate the validation code
            result = eval(validation_code, {"__builtins__": {}}, context)

            return bool(result)

        except Exception as e:
            logger.error(f"Error executing validation code '{validation_code}': {str(e)}")
            # On error, assume validation passes to avoid blocking the app
            return True

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
                            <p class="text-muted mb-4">
                                This page cannot be accessed until the required setup steps are completed.
                            </p>
                            <a href="/admin_dashboard/" class="btn btn-primary">
                                <i class="bi bi-arrow-left me-2"></i>Return to Dashboard
                            </a>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """,
            status=403
        )
