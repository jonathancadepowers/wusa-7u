django.jQuery(document).ready(function($) {
    $('.inline-edit-checkbox').on('change', function() {
        var checkbox = $(this);
        var playerId = checkbox.data('player-id');
        var field = checkbox.data('field');
        var value = checkbox.is(':checked');

        // Get CSRF token
        var csrftoken = $('[name=csrfmiddlewaretoken]').val();

        // Disable checkbox during update
        checkbox.prop('disabled', true);

        $.ajax({
            url: '/admin/players/player/' + playerId + '/update-field/',
            method: 'POST',
            data: {
                field: field,
                value: value,
                csrfmiddlewaretoken: csrftoken
            },
            success: function(response) {
                if (response.success) {
                    // Re-enable checkbox
                    checkbox.prop('disabled', false);
                    // Optional: show brief success indication
                    checkbox.parent().css('background-color', '#d4edda');
                    setTimeout(function() {
                        checkbox.parent().css('background-color', '');
                    }, 500);
                } else {
                    alert('Error updating field: ' + response.error);
                    // Revert checkbox state
                    checkbox.prop('checked', !value);
                    checkbox.prop('disabled', false);
                }
            },
            error: function() {
                alert('Error updating field');
                // Revert checkbox state
                checkbox.prop('checked', !value);
                checkbox.prop('disabled', false);
            }
        });
    });
});
