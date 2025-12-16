def master_password_challenge(request):
    """
    Context processor to add master password challenge flag to all templates.
    """
    return {
        'needs_master_password_challenge': getattr(request, 'needs_master_password_challenge', False)
    }
