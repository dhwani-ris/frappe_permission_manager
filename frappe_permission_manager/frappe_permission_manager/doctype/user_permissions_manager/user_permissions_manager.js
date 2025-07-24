frappe.ui.form.on("User Permissions Manager", {
    refresh(frm) {
        frm.set_query("users", function() {
            let roles_list = (frm.doc.roles || []).map(d => d.role);
            return {
                query: "frappe_permission_manager.frappe_permission_manager.api.user_multiselect_query",
                filters: { roles: JSON.stringify(roles_list) }
            };
        });
    },

    onload(frm) {
        frm.fields_dict["user_permission_manager_mapper"].grid.get_field("allow").get_query = () => {
            return {
                filters: {
                    issingle: 0,
                    istable: 0,
                },
            };
        };

        frm.fields_dict["user_permission_manager_mapper"].grid.get_field("applicable_for").get_query = (doc, cdt, cdn) => {
            const row = locals[cdt][cdn];
            return {
                query: "frappe.core.doctype.user_permission.user_permission.get_applicable_for_doctype_list",
                doctype: row.allow,
            };
        };
    },
});

frappe.ui.form.on("User Permissions Manager Child", {
    allow: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.allow && row.for_value) {
            frappe.model.set_value(cdt, cdn, "for_value", null);
        }

        frappe.ui.form.trigger(cdt, cdn, "toggle_hide_descendants");
    },

    apply_to_all_doctypes: function (frm, cdt, cdn) {
        frappe.ui.form.trigger(cdt, cdn, "set_applicable_for_constraint");
    },

    set_applicable_for_constraint: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.meta.get_docfield("User Permissions Manager Child", "applicable_for", frm.doc.name).reqd = !row.apply_to_all_doctypes;

        if (row.apply_to_all_doctypes && row.applicable_for) {
            frappe.model.set_value(cdt, cdn, "applicable_for", null);
        }
    },

    toggle_hide_descendants: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const show = frappe.boot.nested_set_doctypes.includes(row.allow);

        frappe.meta.get_docfield("User Permissions Manager Child", "hide_descendants", frm.doc.name).hidden = !show;
        frm.refresh_field("user_permission_manager_mapper");
    }
});
    