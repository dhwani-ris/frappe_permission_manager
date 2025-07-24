import frappe
import json

@frappe.whitelist()
def user_multiselect_query(doctype, txt, searchfield, start, page_len, filters):
    roles = filters.get("roles", [])
    if isinstance(roles, str):
        roles = json.loads(roles)

    if not roles:
        roles = []

    if roles:
        return frappe.db.sql("""
            SELECT u.name, u.full_name
            FROM `tabUser` u
            WHERE u.name IN (
                SELECT DISTINCT parent
                FROM `tabHas Role`
                WHERE role IN %(roles)s
            )
            AND u.name LIKE %(txt)s
            LIMIT %(start)s, %(page_len)s
        """, {
            "roles": roles,
            "txt": f"%{txt}%",
            "start": start,
            "page_len": page_len
        })
    else:
        return frappe.db.sql("""
            SELECT u.name, u.full_name
            FROM `tabUser` u
            WHERE u.name LIKE %(txt)s
            LIMIT %(start)s, %(page_len)s
        """, {
            "txt": f"%{txt}%",
            "start": start,
            "page_len": page_len
        })
