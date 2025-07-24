# Frappe Permissions Manager

A powerful Frappe app for bulk management of user permissions with advanced control features for data access and security.

## 🎯 Overview

The Frappe Permissions Manager is a comprehensive application that enables administrators to efficiently manage user permissions across their system. It provides granular control over data access, allowing you to restrict which records users can view and modify based on various criteria.

### Key Benefits

- **Bulk Permission Management**: Apply permissions to multiple users simultaneously
- **Role-Based Access Control**: Automatically assign permissions based on user roles
- **Granular Data Control**: Restrict access to specific records and document types
- **Flexible Configuration**: Support for both global and scoped permissions
- **Real-time Updates**: Permissions take effect immediately upon saving

## ✨ Features

### 🔐 Core Functionality

- **Multi-User Assignment**: Assign permissions to multiple users in a single operation
- **Role-Based Permissions**: Automatically populate users based on selected roles
- **Document Type Control**: Restrict access to specific document types (e.g., Customer, Supplier, Project)
- **Record-Level Security**: Control access to individual records within document types
- **Global vs Scoped Permissions**: Choose between applying permissions globally or to specific document types

### 🎛️ Advanced Controls

- **Default Permissions**: Set default permissions for users
- **Descendant Control**: Option to hide child records of restricted parent records
- **Conflict Detection**: Automatic detection and prevention of conflicting permissions

### 🔄 Dynamic Updates

- **Real-time Permission Refresh**: Permissions are applied immediately upon saving
- **Automatic Cleanup**: Removed permissions are automatically cleaned up
- **Cache Management**: Automatic cache invalidation for updated permissions

## 🚀 Installation

### Prerequisites

- Frappe Framework (v15 or later)

### Installation Steps

1. **Clone the repository**
   ```bash
   bench get-app https://github.com/dhwani-ris/frappe_permission_manager.git --branch <branch-name>
   ```

2. **Install the app**
   ```bash
   bench --site your-site.com install-app user_permissions_manager
   ```

3. **Migrate the database**
   ```bash
   bench --site your-site.com migrate
   ```

4. **Restart the bench**
   ```bash
   bench restart
   ```

### Post-Installation

After installation, you'll find the "User Permissions Manager" module in your Frappe desk under the "User Permissions Manager" section.

## 📖 Usage

### Creating User Permissions

1. **Navigate to User Permissions Manager**
   - Go to Desk → User Permissions Manager → User Permissions Manager

2. **Select Users or Roles**
   - Choose individual users from the "User" table, or
   - Select roles and enable "Apply To Role?" to automatically include all users with those roles

3. **Configure Permissions**
   - In the "Assign Permissions" table, add rows for each permission rule:
     - **Allow**: Select the document type (e.g., Customer, Supplier)
     - **For Value**: Choose the specific record(s) to restrict access to
     - **Apply To All Document Types**: Check to apply globally, uncheck for specific doctypes
     - **Applicable For**: (Optional) Select specific document type when not applying globally
     - **Is Default**: Mark as default permission for the user
     - **Hide Descendants**: Option to hide child records

4. **Save and Apply**
   - Click "Save" to apply the permissions immediately

### Permission Types

#### Individual User Assignment
```json
{
  "users": ["user1@example.com", "user2@example.com"],
  "permissions": [
    {
      "allow": "Customer",
      "for_value": "CUSTOMER-001",
      "apply_to_all_doctypes": true
    }
  ]
}
```

#### Role-Based Assignment
```json
{
  "roles": ["Sales User", "Sales Manager"],
  "apply_to_role": true,
  "permissions": [
    {
      "allow": "Customer",
      "for_value": "CUSTOMER-001",
      "apply_to_all_doctypes": false,
      "applicable_for": "Sales Order"
    }
  ]
}
```

### Use Cases

#### Sales Team Management
- Restrict sales representatives to only see their assigned customers
- Allow sales managers to see all customers but restrict order access

#### Project-Based Access
- Give project managers access only to their assigned projects
- Restrict team members to specific project tasks

#### Multi-Company Setup
- Separate data access between different companies or subsidiaries
- Control cross-company data visibility

## ⚙️ Configuration

### Permission Levels

The app requires **System Manager** role to create and manage user permissions.

### Advanced Settings

#### Cache Management
Permissions are automatically cached for performance. The cache is invalidated when:
- Permissions are updated
- Users are added/removed
- Roles are modified

#### Conflict Resolution
The system automatically detects and prevents:
- Duplicate permission entries
- Conflicting global and scoped permissions
- Multiple default permissions for the same user and document type

## 🧪 Testing

Run the test suite to ensure everything is working correctly:

```bash
bench --site your-site.com run-tests --app user_permissions_manager
```

### Test Coverage

The test suite covers:
- Permission creation and validation
- Role-based user assignment
- Conflict detection
- Default permission handling
- Permission cleanup and updates


## License

MIT License - see [license.txt](license.txt) for details.

## Support & Contributing

- **Publisher**: Dhwani RIS
- **Email**: bhushan.barbuddhe@dhwaniris.com
- **Issues**: Report bugs via GitHub issues
- **PRs Welcome**: Follow pre-commit guidelines

### **Contributing Guidelines**
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Follow code quality standards (pre-commit will help)
4. Test thoroughly on different screen sizes
5. Submit pull request with detailed description

---

**Note**: This app is designed for Frappe Framework v15 and later. For older versions, please check compatibility or upgrade your Frappe installation. 
