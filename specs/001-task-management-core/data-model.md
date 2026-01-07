# Data Model: Core Task Management

## Entities

### User
Represents an individual who owns a task list.

- `id`: UUID (Primary Key)
- `email`: String (Unique, Indexed)
- `hashed_password`: String
- `is_active`: Boolean
- `created_at`: DateTime

### Task
Represents an item to be done.

- `id`: UUID (Primary Key)
- `owner_id`: UUID (Foreign Key to User)
- `title`: String (Non-null, min_length=1, max_length=255)
- `description`: String (Optional, max_length=1000)
- `status`: Enum (pending, completed)
- `priority`: Enum (low, medium, high)
- `created_at`: DateTime (Indexed)
- `updated_at`: DateTime

### Tag
A label for categorizing tasks.

- `id`: UUID (Primary Key)
- `name`: String (Non-null, lowercased, max_length=50)
- `user_id`: UUID (Foreign Key to User - Tags are user-specific)

### TaskTag Association (Many-to-Many)
- `task_id`: UUID (Foreign Key)
- `tag_id`: UUID (Foreign Key)

## Relationships

- **User -> Tasks**: One-to-Many (cascade delete)
- **User -> Tags**: One-to-Many (cascade delete)
- **Task -> Tags**: Many-to-Many (through Association table)

## Validation Rules

- **Strict Titles**: Empty or whitespace-only titles are rejected at the model level.
- **Priority Domain**: Must be one of `low`, `medium`, or `high`.
- **User Isolation**: All queries must filter by `owner_id` (enforced via DB session dependencies).
