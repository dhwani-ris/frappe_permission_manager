# Copyright (c) 2025, Dhwani RIS and contributors
# License: MIT

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.core.doctype.user_permission.user_permission import (
    add_user_permissions,
    clear_user_permissions,
)
from collections import defaultdict


class UserPermissionsManager(Document):
    def validate(self):
        self.validate_strict_user_permission_enabled()
        self.validate_user_permission()
        self.validate_default_permission()
        if self.apply_to_role and not self.roles:
            frappe.throw(_("You must select at least one role when 'Apply to Role' is checked."))

    def validate_strict_user_permission_enabled(self):
        if not frappe.db.get_single_value("System Settings", "apply_strict_user_permissions"):
            frappe.throw(_("Strict User Permissions is not enabled. Please enable it in System Settings."))

    def before_save(self):
        if self.apply_to_role:
            roles = [r.role for r in self.roles or []]
            if not roles:
                frappe.throw(_("No roles selected to populate users."))

            users = frappe.get_all(
                "Has Role",
                filters = {
                    "role": ["in", roles],
                    "parenttype": "User"
                },
                fields=["parent as user"]
            )

            seen_users = set()
            self.users = []
            for u in users:
                if u.user not in seen_users:
                    self.append("users", {"user": u.user})
                    seen_users.add(u.user)
                
        if not self.is_new():
            self._doc_before_save = frappe.get_doc(self.doctype, self.name)

    def after_insert(self):
        apply_bulk_user_permissions(self.name)
        self._trigger_permission_refresh()

    def on_update(self):
        if hasattr(self, '_doc_before_save') and not self.is_new():
            old_doc = self._doc_before_save
            if old_doc:
                previous_users = set([u.user for u in old_doc.users])
                current_users = set(self.get_user_list())
                removed_users = previous_users - current_users

                # Remove only permissions that this doc had created for removed users
                for user in removed_users:
                    for row in old_doc.user_permission_manager_mapper:
                        _safe_clear_permission_entry(user, row)

        # Always delete and reapply for remaining users in this doc
        # delete_user_permissions(self.name)
        apply_bulk_user_permissions(self.name)
        self._trigger_permission_refresh()

    def on_trash(self):
        delete_user_permissions(self.name)
        self._trigger_permission_refresh()

    def validate_user_permission(self):
        seen = set()
        scoped_permissions = defaultdict(set)
        global_permissions = set()

        for row in self.user_permission_manager_mapper:
            for user in self.get_user_list():
                key = (
                    user,
                    row.allow,
                    row.for_value,
                    row.applicable_for or "",
                    row.apply_to_all_doctypes,
                )
                if key in seen:
                    frappe.throw(
                        _("Duplicate rows found for user '{0}' in User Permissions Manager.").format(user),
                        title="Duplicate User Permissions",
                    )
                seen.add(key)

                conflict_key = (row.allow, row.for_value)
                if row.apply_to_all_doctypes:
                    if conflict_key in scoped_permissions:
                        frappe.throw(
                            _("Conflicting global and scoped permissions for '{0}' and value '{1}'.").format(
                                row.allow, row.for_value
                            ),
                            title="Conflicting Permissions",
                        )
                    global_permissions.add(conflict_key)
                else:
                    if conflict_key in global_permissions:
                        frappe.throw(
                            _("Conflicting scoped and global permissions for '{0}' and value '{1}'.").format(
                                row.allow, row.for_value
                            ),
                            title="Conflicting Permissions",
                        )
                    scoped_permissions[conflict_key].add(row.applicable_for)

    def validate_default_permission(self):
        seen = {}
        for row in self.user_permission_manager_mapper:
            if row.is_default:
                for user in self.get_user_list():
                    key = (user, row.allow)
                    if key in seen:
                        frappe.throw(
                            _("Multiple defaults found for user '{0}' and Doctype '{1}'. Only one is allowed.")
                            .format(user, row.allow),
                            title="Multiple Default Permissions",
                        )
                    seen[key] = 1

    def _trigger_permission_refresh(self):
        for u in self.get_user_list():
            frappe.cache.hdel("user_permissions", u)
            frappe.publish_realtime("update_user_permissions", user=u, after_commit=True)

    def get_user_list(self):
        if self.apply_to_role:
            roles = [r.role for r in self.roles or []]
            if not roles:
                frappe.throw(_("No roles selected to apply user permissions."))

            users = frappe.get_all(
                "Has Role",
                filters={
                    "role": ["in", roles],
                    "parenttype": "User"  # Only get User documents, not Reports
                },
                fields=["parent as user"]
            )
            return [u.user for u in users]
        return [u.user for u in self.users or []]


@frappe.whitelist()
def apply_bulk_user_permissions(docname):
    doc = frappe.get_doc("User Permissions Manager", docname)
    users = doc.get_user_list()

    success = 0
    errors = []

    grouped = defaultdict(lambda: {
        "user": None,
        "doctype": None,
        "docname": None,
        "apply_to_all_doctypes": 1,
        "is_default": 0,
        "hide_descendants": 0,
        "applicable_doctypes": []
    })

    for row in doc.user_permission_manager_mapper:
        for user in users:
            key = (user, row.allow, row.for_value)

            entry = grouped[key]
            entry["user"] = user
            entry["doctype"] = row.allow
            entry["docname"] = row.for_value
            entry["is_default"] = row.is_default
            entry["hide_descendants"] = row.hide_descendants

            if not row.apply_to_all_doctypes:
                entry["apply_to_all_doctypes"] = 0
                if row.applicable_for and row.applicable_for not in entry["applicable_doctypes"]:
                    entry["applicable_doctypes"].append(row.applicable_for)

    for key, data in grouped.items():
        existing = frappe.get_all(
            "User Permission",
            filters={
                "user": data["user"],
                "allow": data["doctype"],
                "for_value": data["docname"],
                "apply_to_all_doctypes": data["apply_to_all_doctypes"],
            },
            fields=["name"]
        )

        if data["apply_to_all_doctypes"] == 0:
            existing = frappe.get_all(
                "User Permission",
                filters={
                    "user": data["user"],
                    "allow": data["doctype"],
                    "for_value": data["docname"],
                    "apply_to_all_doctypes": 0,
                },
                fields=["applicable_for"]
            )
            existing_applicable_for = {row["applicable_for"] for row in existing if row["applicable_for"]}
            if set(data["applicable_doctypes"]).issubset(existing_applicable_for):
                continue

        elif existing:
            continue

        try:
            add_user_permissions(data)
            success += 1
        except Exception:
            errors.append(f"{data['user']}: {data['doctype']}/{data['docname']}")

    if success:
        frappe.msgprint(_(f"Applied {success} user permission(s) successfully."))

    if errors:
        frappe.msgprint(_("Some errors occurred:<br>") + "<br>".join(errors))

    return {"success": success, "errors": errors}


def delete_user_permissions(docname):
    doc = frappe.get_doc("User Permissions Manager", docname)
    for user in doc.get_user_list():
        for row in doc.user_permission_manager_mapper:
            _safe_clear_permission_entry(user, row)


def _safe_clear_permission_entry(user, row):
    filters = {
        "user": user,
        "allow": row.allow,
        "for_value": row.for_value,
    }
    if row.apply_to_all_doctypes:
        filters["apply_to_all_doctypes"] = 1
    else:
        filters["apply_to_all_doctypes"] = 0
        filters["applicable_for"] = row.applicable_for

    frappe.db.delete("User Permission", filters)
