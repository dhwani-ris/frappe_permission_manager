import frappe
from frappe.tests.utils import FrappeTestCase
from user_permissions_manager.user_permissions_manager.doctype.user_permissions_manager.user_permissions_manager import (
    apply_bulk_user_permissions, delete_user_permissions
)

class TestUserPermissionsManager(FrappeTestCase):
    def setUp(self):
        self.test_user = "test-user@example.com"
        self.second_user = "second-user@example.com"
        self.note_title = "Test Note"

        for user in [self.test_user, self.second_user]:
            if not frappe.db.exists("User", user):
                frappe.get_doc({
                    "doctype": "User",
                    "email": user,
                    "first_name": "Test User",
                    "send_welcome_email": 0
                }).insert(ignore_permissions=True)

        if not frappe.db.exists("Note", self.note_title):
            frappe.get_doc({
                "doctype": "Note",
                "title": self.note_title,
                "content": "Content for testing"
            }).insert()

        self.note = frappe.get_doc("Note", {"title": self.note_title})

    def tearDown(self):
        frappe.db.delete("User Permissions Manager")
        frappe.db.delete("User Permission", {"user": ["in", [self.test_user, self.second_user]]})
        frappe.db.delete("Note", {"title": ["in", ["Test Note", "Another Note", "Note A", "Note B", "Updated Note"]]})
        frappe.db.delete("User", {"email": ["in", [self.test_user, self.second_user]]})
        frappe.db.commit()

    def test_single_permission_applies(self):
        doc = frappe.get_doc({
            "doctype": "User Permissions Manager",
            "users": [{"user": self.test_user}],
            "user_permission_manager_mapper": [{
                "allow": "Note",
                "for_value": self.note.name,
                "apply_to_all_doctypes": 1
            }]
        }).insert()
        self.assertTrue(frappe.db.exists("User Permission", {
            "user": self.test_user,
            "allow": "Note",
            "for_value": self.note.name
        }))

    def test_duplicate_rows_blocked(self):
        doc = frappe.get_doc({
            "doctype": "User Permissions Manager",
            "users": [{"user": self.test_user}],
            "user_permission_manager_mapper": [
                {
                    "allow": "Note",
                    "for_value": self.note.name,
                    "apply_to_all_doctypes": 1
                },
                {
                    "allow": "Note",
                    "for_value": self.note.name,
                    "apply_to_all_doctypes": 1
                }
            ]
        })
        with self.assertRaises(frappe.ValidationError):
            doc.insert()

    def test_multiple_applicable_for_grouped(self):
        doc = frappe.get_doc({
            "doctype": "User Permissions Manager",
            "users": [{"user": self.test_user}],
            "user_permission_manager_mapper": [
                {
                    "allow": "Note",
                    "for_value": self.note.name,
                    "apply_to_all_doctypes": 0,
                    "applicable_for": "ToDo"
                },
                {
                    "allow": "Note",
                    "for_value": self.note.name,
                    "apply_to_all_doctypes": 0,
                    "applicable_for": "Event"
                }
            ]
        }).insert()
        self.assertTrue(frappe.db.exists("User Permission", {
            "user": self.test_user,
            "allow": "Note",
            "for_value": self.note.name,
            "applicable_for": "ToDo"
        }))
        self.assertTrue(frappe.db.exists("User Permission", {
            "user": self.test_user,
            "allow": "Note",
            "for_value": self.note.name,
            "applicable_for": "Event"
        }))

    def test_default_conflict_detection(self):
        another_note = frappe.get_doc({
            "doctype": "Note",
            "title": "Another Note",
            "content": "Note 2"
        }).insert()
        doc = frappe.get_doc({
            "doctype": "User Permissions Manager",
            "users": [{"user": self.test_user}],
            "user_permission_manager_mapper": [
                {
                    "allow": "Note",
                    "for_value": self.note.name,
                    "is_default": 1,
                    "apply_to_all_doctypes": 1
                },
                {
                    "allow": "Note",
                    "for_value": another_note.name,
                    "is_default": 1,
                    "apply_to_all_doctypes": 1
                }
            ]
        })
        with self.assertRaises(frappe.ValidationError):
            doc.insert()

    def test_permission_cleanup_on_trash(self):
        doc = frappe.get_doc({
            "doctype": "User Permissions Manager",
            "users": [{"user": self.test_user}],
            "user_permission_manager_mapper": [{
                "allow": "Note",
                "for_value": self.note.name,
                "apply_to_all_doctypes": 1
            }]
        }).insert()
        self.assertTrue(frappe.db.exists("User Permission", {
            "user": self.test_user,
            "for_value": self.note.name
        }))
        delete_user_permissions(doc.name)
        self.assertFalse(frappe.db.exists("User Permission", {
            "user": self.test_user,
            "for_value": self.note.name
        }))

    def test_edge_missing_for_value(self):
        doc = frappe.get_doc({
            "doctype": "User Permissions Manager",
            "users": [{"user": self.test_user}],
            "user_permission_manager_mapper": [{
                "allow": "Note",
                "apply_to_all_doctypes": 1
            }]
        })
        with self.assertRaises(frappe.MandatoryError):
            doc.insert()

    def test_hide_descendants_flag_set(self):
        doc = frappe.get_doc({
            "doctype": "User Permissions Manager",
            "users": [{"user": self.test_user}],
            "user_permission_manager_mapper": [{
                "allow": "Note",
                "for_value": self.note.name,
                "hide_descendants": 1,
                "apply_to_all_doctypes": 1
            }]
        }).insert()
        perm = frappe.get_doc("User Permission", {
            "user": self.test_user,
            "for_value": self.note.name
        })
        self.assertEqual(perm.hide_descendants, 1)

    def test_permission_does_not_duplicate_on_reapply(self):
        doc = frappe.get_doc({
            "doctype": "User Permissions Manager",
            "users": [{"user": self.test_user}],
            "user_permission_manager_mapper": [{
                "allow": "Note",
                "for_value": self.note.name,
                "apply_to_all_doctypes": 1
            }]
        })
        doc.flags.ignore_after_insert = True
        doc.insert()
        apply_bulk_user_permissions(doc.name)
        result = apply_bulk_user_permissions(doc.name)
        self.assertEqual(result["success"], 0)

    def test_multiple_users_same_value(self):
        doc = frappe.get_doc({
            "doctype": "User Permissions Manager",
            "users": [{"user": self.second_user}],
            "user_permission_manager_mapper": [{
                "allow": "Note",
                "for_value": self.note.name,
                "apply_to_all_doctypes": 1
            }]
        }).insert()
        self.assertTrue(frappe.db.exists("User Permission", {
            "user": self.second_user,
            "for_value": self.note.name
        }))

    def test_conflicting_scoped_and_global(self):
        doc_scoped = frappe.get_doc({
            "doctype": "User Permissions Manager",
            "users": [{"user": self.test_user}],
            "user_permission_manager_mapper": [{
                "allow": "Note",
                "for_value": self.note.name,
                "apply_to_all_doctypes": 0,
                "applicable_for": "ToDo"
            }]
        }).insert()

        doc_global = frappe.get_doc({
            "doctype": "User Permissions Manager",
            "users": [{"user": self.test_user}],
            "user_permission_manager_mapper": [{
                "allow": "Note",
                "for_value": self.note.name,
                "apply_to_all_doctypes": 1
            }]
        })
        doc_global.flags.ignore_after_insert = True
        doc_global.insert()
        apply_bulk_user_permissions(doc_global.name)

        self.assertTrue(frappe.db.exists("User Permission", {
            "user": self.test_user,
            "for_value": self.note.name,
            "apply_to_all_doctypes": 1
        }))
        self.assertFalse(frappe.db.exists("User Permission", {
            "user": self.test_user,
            "for_value": self.note.name,
            "applicable_for": "ToDo"
        }))

    def test_apply_to_all_removed_on_scoped_insert(self):
        global_doc = frappe.get_doc({
            "doctype": "User Permissions Manager",
            "users": [{"user": self.test_user}],
            "user_permission_manager_mapper": [{
                "allow": "Note",
                "for_value": self.note.name,
                "apply_to_all_doctypes": 1
            }]
        }).insert()

        scoped_doc = frappe.get_doc({
            "doctype": "User Permissions Manager",
            "users": [{"user": self.test_user}],
            "user_permission_manager_mapper": [{
                "allow": "Note",
                "for_value": self.note.name,
                "apply_to_all_doctypes": 0,
                "applicable_for": "ToDo"
            }]
        })
        scoped_doc.flags.ignore_after_insert = True
        scoped_doc.insert()
        apply_bulk_user_permissions(scoped_doc.name)

        self.assertFalse(frappe.db.exists("User Permission", {
            "user": self.test_user,
            "for_value": self.note.name,
            "apply_to_all_doctypes": 1
        }))
        self.assertTrue(frappe.db.exists("User Permission", {
            "user": self.test_user,
            "for_value": self.note.name,
            "applicable_for": "ToDo"
        }))

    def test_conflicting_multiple_rows(self):
        doc = frappe.get_doc({
            "doctype": "User Permissions Manager",
            "users": [{"user": self.test_user}],
            "user_permission_manager_mapper": [
                {
                    "allow": "Note",
                    "for_value": self.note.name,
                    "apply_to_all_doctypes": 1
                },
                {
                    "allow": "Note",
                    "for_value": self.note.name,
                    "apply_to_all_doctypes": 0,
                    "applicable_for": "Event"
                }
            ]
        })
        with self.assertRaises(frappe.ValidationError):
            doc.insert()

    def test_scoped_then_global_overwrites(self):
        scoped_doc = frappe.get_doc({
            "doctype": "User Permissions Manager",
            "users": [{"user": self.test_user}],
            "user_permission_manager_mapper": [
                {
                    "allow": "Note",
                    "for_value": self.note.name,
                    "apply_to_all_doctypes": 0,
                    "applicable_for": "ToDo"
                }
            ]
        }).insert()

        global_doc = frappe.get_doc({
            "doctype": "User Permissions Manager",
            "users": [{"user": self.test_user}],
            "user_permission_manager_mapper": [
                {
                    "allow": "Note",
                    "for_value": self.note.name,
                    "apply_to_all_doctypes": 1
                }
            ]
        })
        global_doc.flags.ignore_after_insert = True
        global_doc.insert()
        apply_bulk_user_permissions(global_doc.name)

        self.assertTrue(frappe.db.exists("User Permission", {
            "user": self.test_user,
            "for_value": self.note.name,
            "apply_to_all_doctypes": 1
        }))
        self.assertFalse(frappe.db.exists("User Permission", {
            "user": self.test_user,
            "for_value": self.note.name,
            "applicable_for": "ToDo"
        }))

    def test_mixed_default_and_non_default(self):
        note_a = frappe.get_doc({"doctype": "Note", "title": "Note A", "content": "test"}).insert()
        note_b = frappe.get_doc({"doctype": "Note", "title": "Note B", "content": "test"}).insert()

        doc = frappe.get_doc({
            "doctype": "User Permissions Manager",
            "users": [{"user": self.test_user}],
            "user_permission_manager_mapper": [
                {
                    "allow": "Note",
                    "for_value": note_a.name,
                    "is_default": 1,
                    "apply_to_all_doctypes": 1
                },
                {
                    "allow": "Note",
                    "for_value": note_b.name,
                    "is_default": 0,
                    "apply_to_all_doctypes": 1
                }
            ]
        }).insert()

        self.assertTrue(frappe.db.exists("User Permission", {
            "user": self.test_user,
            "for_value": note_a.name,
            "is_default": 1
        }))
        self.assertTrue(frappe.db.exists("User Permission", {
            "user": self.test_user,
            "for_value": note_b.name
        }))

    def test_bulk_duplicate_protection_multiple_docs(self):
        doc1 = frappe.get_doc({
            "doctype": "User Permissions Manager",
            "users": [{"user": self.test_user}],
            "user_permission_manager_mapper": [{
                "allow": "Note",
                "for_value": self.note.name,
                "apply_to_all_doctypes": 1
            }]
        }).insert()

        doc2 = frappe.get_doc({
            "doctype": "User Permissions Manager",
            "users": [{"user": self.test_user}],
            "user_permission_manager_mapper": [{
                "allow": "Note",
                "for_value": self.note.name,
                "apply_to_all_doctypes": 1
            }]
        })
        doc2.flags.ignore_after_insert = True
        doc2.insert()
        result = apply_bulk_user_permissions(doc2.name)
        self.assertEqual(result["success"], 0)

    

    def test_toggle_apply_to_all_doctypes_on_update(self):
        doc = frappe.get_doc({
            "doctype": "User Permissions Manager",
            "users": [{"user": self.test_user}],
            "user_permission_manager_mapper": [{
                "allow": "Note",
                "for_value": self.note.name,
                "apply_to_all_doctypes": 1
            }]
        }).insert()

        doc.user_permission_manager_mapper[0].apply_to_all_doctypes = 0
        doc.user_permission_manager_mapper[0].applicable_for = "ToDo"
        doc.save()

        self.assertFalse(frappe.db.exists("User Permission", {
            "user": self.test_user,
            "for_value": self.note.name,
            "apply_to_all_doctypes": 1
        }))
        self.assertTrue(frappe.db.exists("User Permission", {
            "user": self.test_user,
            "for_value": self.note.name,
            "applicable_for": "ToDo"
        }))

    
