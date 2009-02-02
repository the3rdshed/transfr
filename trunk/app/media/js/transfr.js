$.durl = function(name, args, full) {
    var out = $.durls[name] || false;
    if (out && args) {
        for (var key in args) {
            var token = '%'+key;
            if (out.match(token)) out = out.replace(token, args[key]);
            else out = out + (out.match(/\?\w+\=/) ?'&':'?') + key + '=' + args[key];
        }
    }
    return out;
};
var poll = false;
$.transfr = {
    init: function() {

        if ($.browser.msie) { // *Thanks* IE for making me do stupid things like this
            $('.ui-tablegrid').ready(function(){ $(this).width($(this).parent().width()-4); });
        }

        $('#transfr-file-upload-wrapper').hide();
        
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
                $.stop(e);
                return false;
            }
        });

        $('.ui-button-submit').live('click', function(){
            $(this).parents('form').submit();
        });

        $('#transfr-file-upload .ui-button-reset').live('click', function(){
            $('#transfr-file-upload-wrapper').hide();
            $('#transfr-file-upload').text('');
            $('#transfr-file-preview-wrapper, #transfr-folder-list-wrapper').show();
        });

        // mouseover effects
        $('.ui-tablegrid-drawer, .ui-tablegrid tbody tr').hover(
            function(){ $(this).addClass('hover'); }, 
            function(){ $(this).removeClass('hover'); }
        );

        // folder selection
        $('tr.folder').click(function(e){
            $.transfr.folder.open(this, e);
            $('input[type=checkbox]').attr('checked', '').trigger('change');
        }).filter(':first').click();

        // file selection
        $('tr.file').click(function(e){
            if (!$(this).hasClass('active')) {
                $('#transfr-file-preview-wrapper, #transfr-folder-list-wrapper').show('fast');
                $('#transfr-file-upload-wrapper').hide();
                $.transfr.file.preview($.transfr.getId(this, 'file'));
                $(this).addClass('active').siblings('tr').removeClass('active');
            }
        }).filter(':first').click();

        if (!$('tr.file:first').get(0)) {
            $('#transfr-file-preview-wrapper').hide();
        }
        
        /*
        $('.transf-upload-file').click(function(e){
            var url = $(this).attr('href') + ' #transfr-file-upload';
            $('#transfr-file-preview-wrapper, #transfr-folder-list-wrapper').hide('fast');
            $('#transfr-file-upload').load(url, function(){
                if ($('#leftbar').is(':hidden')) {
                    $('.ui-tablegrid-drawer').click();
                }
                $('#transfr-file-upload-wrapper').show();
            });
            e.preventDefault(e);
            return $.stop(e);
        });
        */
        
        $('.transfr-delete-file').click(function(e){
            var id = $.transfr.getId(this, 'file');
            $.transfr.file.remove([id], [$(this).parents('tr:first')]);
            return $.stop(e);
        });

        // multiple delete
        $('.transfr-delete-selection').click(function(e){
            var checked = $('.file-check-single:checked');
            var ids = [];
            var trs = [];
            checked.each(function(){
                trs.push($(this).parents('tr:first'));
                ids.push(this.value);
            });
            $.transfr.file.remove(ids);
            $('.file-check-all').attr('checked', false);
            return $.stop(e);
        });

        // toggle all checkboxes in file list
        $('.file-check-all').click(function () {
            $('.check-' + this.value).attr('checked', $(this).attr('checked')).trigger('change');
        });

        // Folder list drawer
        if (!$.user.is_superuser) { $('#transfr-folder-list-wrapper').hide(); }
        $('.ui-tablegrid-drawer').addClass('ui-arrow-left-default').hover(
        function(){ $(this).get(0).className = $(this).get(0).className.replace('default', 'hover');}, 
        function(){ $(this).get(0).className = $(this).get(0).className.replace('hover', 'default');})
        .click(function(){
            if ($(this).prev().is(':visible')) {
                $(this).prev().hide();
                $(this).removeClass('ui-arrow-left-default ui-arrow-left-hover').addClass('ui-arrow-right-default');
            }
            else {
                $(this).prev().show();
                $(this).removeClass('ui-arrow-right-default ui-arrow-right-hover').addClass('ui-arrow-left-default');
            }
        });

        if (!$.user.is_superuser && $('tr.file').length < 1) {
            $('.ui-tablegrid-drawer').click();
        }
    },

    getId: function(node, type) {
        var type  = type == 'file' && 'file' || 'folder';
        if ($(node).hasClass(type)) {
            var match = $(node).attr('id').match(/\d+/gi);
        }
        else {
            var match = $(node).parents('.'+type).attr('id').match(/\d+/gi);
        }
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
                $.getJSON($.durl('upload_progress'), {'filename': sessId}, function(data, status) {
                    if (data.finished == true) {
                        progressbar.progressbar('progress', interval);
                        $('div.warning-msg').insertAfter(progressbar).slideDown();
                        clearInterval(poll);
                    }
                    else if (status == 'success') {
                        var progress = parseInt((parseInt(data.uploaded, 10) / parseInt(data.total, 10)) * 100, 10);
                        $('#current-file').text(data.current_file);
                        progressbar.progressbar('progress', progress);
                    }
                });
            };
            poll = setInterval(updateUploadProgress, 1000);
        },
        preview: function(id) {
            if ($('#transfr-file-preview-wrapper').get(0)) {
                var href = $('#file-'+ id +' a.file-download').attr('href');
                $('.transfr-file-preview').addClass('loading');
                $.getJSON($.durl('view_thumbnail', {id: id}), function(json, success){
                    if (success) {
                        var thumb = $('<img class="transfr-file-thumbnail" border="0" />').attr('src', json.thumbnail).hide();
                        var link  = $('<a class="transfr-file-thumb-link" />').attr({href: json.file, title: json.name}).html(thumb);

                        $('.transfr-file-preview').html(link)
                            .animate({height: json.height}, function() {
                                setTimeout(function(){
                                    $('.transfr-file-preview').removeClass('loading');
                                    thumb.fadeIn('normal');
                                }, 100);
                            });
                    }
                });
            }
        },
        remove: function(ids) {
            if (confirm(ngettext('Do you really want to delete this file?', 
                                 'Do you really want to delete these files?',
                                 ids.length))) {
                $.post($.durl('delete_file'), {'ids': ids}, function(data){
                    var folder = $('#transfr-folder-'+ data[0]);
                    $('.transfr-folder-count', folder).text(data[1]);
                    $('.transfr-folder-size', folder).text(data[2]);
                    $.each(ids, function(i, id) { $('#file-'+ id).remove(); });
                }, 'json');
            }
        }
    },
    folder: {
        open: function(el, e) {
            var id = $.transfr.getId(el, 'folder');
            var wrapper = $('#transfr-folder-content-'+id);
            if (wrapper.get(0)) {
                wrapper.show().siblings('div').hide();
                $(el).addClass('active').siblings().removeClass('active');
                $('#title-bar').text($.format('Files of {0:s}', $('.transfr-folder', el).text()));
                $('.file:first', wrapper).click();
            }
        }
    }
};
$($.transfr.init);
