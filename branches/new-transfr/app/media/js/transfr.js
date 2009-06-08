var poll = false;
$.transfr = {
    init: function() {

        // Language switcher
        $('#i18n-switcher').change(function(){
            $(this).parents('form').submit();
        });

        // File upload
        $('form[enctype=multipart/form-data]').bind('submit', function(e){ 
            if (!$.data(this, 'submitted')) { 
                $.transfr.file.upload(this);
                $.data(this, 'submitted', true);
            } // Prevent multiple submits
            else {
                return false;
            }
        });

        // multiple delete
        $('.transfr-delete-selection').click(function(e){
            var checked = $('.file-check:checked');
            if (checked.length === 0) {
                return;
            }
            var ids = [];
            var trs = [];
            checked.each(function(){
                trs.push($(this).parents('tr:first'));
                ids.push(this.value);
            });
            $.transfr.file.remove(ids);
            $('.file-check-all').attr('checked', false);
        });

        // toggle all checkboxes in file list
        $('.file-check-all').click(function () {
            $('.file-check').attr('checked', $(this).attr('checked')).trigger('change');
        });

    },

    getId: function(node) {
        var match = $(node).parents('tr').attr('id').match(/\d+/g);
        return match && match[0] || false;
    },

    file: {
        upload: function(form){
            var sessId = $('.transfr-file-upload-id', form);
            if (!sessId.val()) { return; }
            var interval    = 700;
            var progress    = 0;
            var filename    = $('input[type=file]', form).val() 
            var progressbar = $('<div id="progressbar"></div>').insertAfter($('#additional-form', form)).progressbar();
            var current_file = $('<div id="current-file"></div>').insertAfter($('#additional-form', form));
                
            var updateUploadProgress = function() {
                $.getJSON($urls['upload_progress'], {'filename': sessId}, function(data, status_) {
                    if (data.finished === true) {
                        progressbar.progressbar('value', interval);
                        clearInterval(poll);
                    }
                    else if (status_ === 'success') {
                        var progress = parseInt((parseInt(data.uploaded, 10) / parseInt(data.total, 10)) * 100, 10);
                        console.log(progress);
                        $('#current-file').text(data.current_file);
                        progressbar.progressbar('value', progress);
                    }
                });
            };
            poll = setInterval(updateUploadProgress, 1000);
        },
        remove: function(ids) {
            if (confirm(ngettext('Do you really want to delete this file?', 
                                 'Do you really want to delete these files?',
                                 ids.length))) {
                $.post($urls['delete_file'], {'ids': ids}, function(data){
                    $('#transfr-folder-count').text(data[0]);
                    $('#transfr-folder-size').text(data[1]);
                    $.each(ids, function(i, id) { $('#file-'+ id).remove(); });
                }, 'json');
            }
        }
    }
};
$($.transfr.init);
