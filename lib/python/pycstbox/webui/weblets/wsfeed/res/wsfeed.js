var _i18n = {
    "save_ok" : _("Save successful"),
    "save_err" : _("Save failure"),
    "fld_required" : _("This field is required."),
    "fld_positive" : _("Value must be a positive integer."),
    "fld_number" : _("Value must be a number."),
    "yes": _("Yes"),
    "no": _("No"),
    "ok": _("OK"),
    "cancel": _("Cancel"),
}

function makeSvcUrl(svcName) {
    return document.location.href + '/' + svcName;
}

$(document).ready(function() {
    $(".status").status();
    $("button").button();
    $("[lang]").localize_html(_lang_);

    var edited_variable = null;
    var var_name_displays = $(".var_name_display");
    var form_var_def = $("#var-definition");
    var notice = $("#notice");
    var var_list = $("#var-list");
    var fld_var_type = $('#var_type');
    var fld_var_unit = $('#var_unit');
    var fld_var_threshold = $('#var_threshold');
    var fld_var_ttl = $('#var_ttl');
    var jst_var_list;
    var msg_cfg_changed = $("#msg-cfg_changed");
    var msg_fatal_error = $("#msg-fatal_error");

    $.ajax({
        url: makeSvcUrl('vardefs'),
        success: function(data) {
            nodes = make_jstree_nodes(data)
            setup_jstree(nodes);
        }
    });

    function make_jstree_nodes(data) {
        var nodes = [];

        for (var name in data) {
            var node = {
                text: name,
                id: name,
                icon: false,
                data: data[name]
            };
            nodes.push(node);
        }

        return nodes;
    }

    function setup_jstree(nodes) {
        jst_var_list = var_list.jstree({
            "core": {
                "multiple": false,
                "check_callback": true,
                "themes": {
                    "icons": false
                },
                "sorted": true,
                "data": nodes
            },
            "plugins": ["sort", "unique", "wholerow"]

        }).on("select_node.jstree", function (e, data){
            edited_variable = data.node.data;

            edited_variable.name = data.node.id;
            fld_var_type.val(edited_variable.var_type);
            fld_var_unit.val(edited_variable.unit);
            fld_var_threshold.val(edited_variable.threshold);
            fld_var_ttl.val(edited_variable.ttl);

            var_name_displays.text(edited_variable.name);

            form_var_def.show();
            notice.hide();
        });
        jst_var_list = $.jstree.reference(jst_var_list);
    }

    var inp_var_name = $("#inp-var_name");
    var btn_add_var = $("#btn-add");

    inp_var_name.keyup(function(event) {
        if (event.keyCode == 37 ||  // left arrow
            event.keyCode == 39     // right arrow
        ) return true;

        if (event.keyCode != 8 &&   // backspace
            event.keyCode != 46     // suppr
        ) {
            var char = String.fromCharCode(event.which);
            if (!char.match(/^[A-Za-z0-9_\.]+$/)) {
                event.preventDefault();
                return false;
            }
        }

        btn_add_var.prop("disabled", this.value == '');
        btn_add_var.button('refresh');
    });
    btn_add_var.prop("disabled", true);
    btn_add_var.button('refresh');
    inp_var_name.val("");

    btn_add_var.click(function(){
        var var_name = inp_var_name.val();
        jst_var_list.create_node(
            '#', {
                id: var_name,
                text: var_name,
                data: {
                    var_type: '',
                    unit: '',
                    threshold: 0,
                    ttl: 7200
                }
            },
            'last'
        );
        msg_cfg_changed.show();
    });

    var dlg_delete = null;

    $("#btn-delete").click(function(){
        if (dlg_delete == null) {
            dlg_delete = $("#dlgConfirmDelete").dialog({
                autoOpen: false,
                resizable: false,
                width: 400,
                modal: true,
                dialogClass: "ui-dialog-bkgnd",
                buttons: [{
                    text: _i18n["yes"],
                    click: function () {
                        $(this).dialog("close");
                        if (jst_var_list.delete_node(edited_variable.name)) {
                            msg_cfg_changed.show();
                        } else {
                            alert("Command failed");
                        }
                    }
                }, {
                    text: _i18n["no"],
                    click: function () {
                        $(this).dialog("close");
                    }
                }]
            });
        }
        dlg_delete.dialog('open');
    });

    var progress_indicator = $("#progress-modal");
    progress_indicator.dialog({
        autoOpen: false,
        closeOnEscape: false,

        modal: true
    });

    function info(msg) {
        $("#status").status("info", msg);
    }
    
    function error(msg) {
        $("#status").status("error", msg);
    }
    
    $.extend($.validator.messages, {
        required: _i18n['fld_required'],
        number: _i18n['fld_number'],
        positive: _i18n['fld_positive'],
    });

    $.validator.addMethod("positive",
        function(value, element) {
            return this.optional(element) || /^[0-9]+$/i.test(value);
        }, _i18n['fld_positive']);

    form_var_def.validate({
        //debug : true,
        ignore : ".ignore",
        submitHandler : function(form) {
            console.log(form);
            $.ajax({
                url: document.location.href + '/save',
                data : $(form).serialize(),
                dataType: "json",
                success: function(data){
                    info(_i18n['save_ok'])
                },
                error: function(jqXHR, textStatus, errorThrown){
                    var report = $.parseJSON(jqXHR.responseText);
                    var additInfos = report.additInfos.split('\n', 1);
                    error($.format(_i18n['save_err'] + " ({0})", additInfos[0]));
                }
            });
        },
        onfocusout : false,
        onkeyup : false,
        onclick : false,
        errorElement: "p"
    });

    var var_list_top = $("#var-list-header").height() + 20;
    var var_list_panel = $("#var-list-panel");

    function resize_var_list() {
        var_list.height(var_list_panel.innerHeight() - var_list_top);
    }

    $(window).resize(resize_var_list);
    resize_var_list();

    function fatalError(message, additInfos) {
        $("#fatal-error-msg").status("error", message);
        var additInfosDisplay = $("#fatal-error-additInfos-display");
        if (additInfos != null) {
            var txt = "";
            for (var i = 0; i < additInfos.length; i++) {
                txt += '<p>' + additInfos[i] + '</p>';
            }
            $("#additInfos-text").html(txt);
            additInfosDisplay.show();
        } else {
            $("#additInfos-text").empty();
            additInfosDisplay.hide();
        }
        msg_fatal_error.show();
    }

});

