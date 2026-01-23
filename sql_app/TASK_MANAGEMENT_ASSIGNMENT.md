# Task Management System - SQLAlchemy & PostgreSQL Assignment

## Overview
Build a **Task Management System** API using FastAPI, SQLAlchemy, and PostgreSQL. This assignment will test your understanding of database modeling, migrations, CRUD operations, complex queries, and transaction management.

**Estimated Time:** 2-3 hours  
**Difficulty:** Moderate  
**Type:** Individual Assignment

---

## Project Description

Extend the existing `sql_app` project by building a complete task management system where users can create projects, manage tasks, assign team members, add comments, and organize tasks with tags.

---

## Database Schema Requirements

### Tables to Create (5 new tables)

**1. Projects**
- Unique identifier
- Name (required, 3-100 characters)
- Description (optional, max 500 characters)
- Owner (foreign key to existing User table)
- Budget (decimal, optional)
- Status (active/archived/completed)
- Created and updated timestamps

**2. Tasks**
- Unique identifier
- Title (required, 3-100 characters)
- Description (optional, max 1000 characters)
- Status (todo/in_progress/done)
- Priority (low/medium/high)
- Due date (optional, cannot be in the past)
- Project (foreign key to Projects)
- Created by (foreign key to existing User table)
- Created and updated timestamps

**3. Task Assignments** (Many-to-Many)
- Task ID
- User ID (who is assigned)
- Role on task (owner/contributor/reviewer)
- Assigned at timestamp

**4. Tags**
- Unique identifier
- Name (required, unique, max 50 characters)
- Color (hex color code)

**5. Task Tags** (Many-to-Many)
- Task ID
- Tag ID

**6. Task Comments**
- Unique identifier
- Task ID
- User ID (who commented)
- Content (required, max 500 characters)
- Created timestamp

---

## Required Features

### Core CRUD Operations

**Projects:**
- Create new project
- Get all projects (with pagination)
- Get single project by ID
- Update project
- Delete project (soft delete - archive)

**Tasks:**
- Create new task
- Get all tasks (with filtering and sorting)
- Get single task by ID
- Update task (partial updates supported)
- Delete task
- Bulk create tasks

**Assignments:**
- Assign user(s) to task
- Remove user from task
- Get all users assigned to a task
- Get all tasks assigned to a user

**Tags:**
- Create tag
- Get all tags
- Add tag(s) to task
- Remove tag from task

**Comments:**
- Add comment to task
- Get all comments for a task
- Delete comment

---

## Complex Query Requirements

Implement the following advanced queries:

### Aggregations & Analytics
1. **Project Statistics** - Get count of tasks by status for each project
2. **User Workload** - Get number of tasks assigned to each user
3. **Overdue Tasks Count** - Count of overdue tasks per project
4. **Tasks by Priority** - Distribution of tasks across priority levels

### Multi-table Joins
5. **Task Details** - Get task with project info, assignees, tags, and comments in one query
6. **Project Dashboard** - Get project with all tasks, assignees, and completion percentage

### Filtering & Sorting
7. **Advanced Task Search** - Filter tasks by:
   - Status
   - Priority
   - Due date range (this week, overdue, etc.)
   - Assigned user
   - Project
   - Tags (tasks with specific tag)
   - Sort by: due_date, priority, created_at

8. **User Dashboard** - Get all tasks assigned to a user grouped by project

### Date-based Queries
9. **Tasks Due This Week** - Get all tasks due in the next 7 days
10. **Overdue Tasks** - Get all tasks past their due date and still not completed

---

## Transaction Management Requirements

Implement these operations with proper transaction handling:

### 1. Create Project with Initial Tasks (Rollback on Error)
- Create a project
- Create multiple tasks for that project
- If any task creation fails, rollback entire operation
- Return appropriate error message

### 2. Bulk Task Assignment (Batch Operation)
- Assign multiple users to multiple tasks in one operation
- Use batch insert for performance
- Handle duplicate assignments gracefully

### 3. Complete Task with Side Effects
- Update task status to "done"
- Add automatic comment "Task completed by [user]"
- Update project statistics
- All operations must succeed or all must fail

### 4. Transfer Tasks Between Projects
- Move all tasks from one project to another
- Update all task records
- Create audit trail (comments on each task)
- Ensure data consistency

---

## Alembic Migration Requirements

Create migrations for:
1. **Initial migration** - Create all 5 new tables with relationships
2. **Add indexes** - Add indexes on frequently queried columns (status, priority, due_date)
3. **Add audit columns** - Add created_at and updated_at to all tables
4. **Modify constraints** - Add check constraint ensuring due_date is after created_at

---

## API Endpoints to Implement

### Projects (5 endpoints)
- `POST /projects/` - Create project
- `GET /projects/` - List all projects (with pagination)
- `GET /projects/{project_id}` - Get project details
- `PUT /projects/{project_id}` - Update project
- `DELETE /projects/{project_id}` - Archive/delete project

### Tasks (8 endpoints)
- `POST /tasks/` - Create task
- `POST /tasks/bulk` - Bulk create tasks
- `GET /tasks/` - List tasks with filtering
- `GET /tasks/{task_id}` - Get task details
- `PUT /tasks/{task_id}` - Update task
- `DELETE /tasks/{task_id}` - Delete task
- `PUT /tasks/{task_id}/status` - Update task status
- `POST /tasks/{task_id}/complete` - Mark task as complete (with transaction)

### Assignments (3 endpoints)
- `POST /tasks/{task_id}/assign` - Assign user(s) to task
- `DELETE /tasks/{task_id}/assign/{user_id}` - Unassign user
- `GET /tasks/{task_id}/assignees` - Get all assignees

### Tags (3 endpoints)
- `POST /tags/` - Create tag
- `GET /tags/` - List all tags
- `POST /tasks/{task_id}/tags` - Add tag(s) to task

### Comments (2 endpoints)
- `POST /tasks/{task_id}/comments` - Add comment
- `GET /tasks/{task_id}/comments` - Get all comments

### Analytics (5 endpoints)
- `GET /analytics/project-stats` - Project statistics
- `GET /analytics/user-workload` - User workload report
- `GET /analytics/overdue-tasks` - Overdue tasks report
- `GET /tasks/due-this-week` - Tasks due in next 7 days
- `GET /users/{user_id}/dashboard` - User's task dashboard

---

## Pydantic Models Required

Create Pydantic schemas for:

**Projects:**
- ProjectCreate
- ProjectUpdate
- ProjectResponse
- ProjectWithStats

**Tasks:**
- TaskCreate
- TaskUpdate
- TaskResponse
- TaskDetailResponse (includes project, assignees, tags)
- TaskBulkCreate

**Assignments:**
- TaskAssignmentCreate
- TaskAssignmentResponse

**Tags:**
- TagCreate
- TagResponse

**Comments:**
- CommentCreate
- CommentResponse

---

## Validation Requirements

Implement these validations:

**Tasks:**
- Title: 3-100 characters
- Description: max 1000 characters
- Status: must be one of (todo, in_progress, done)
- Priority: must be one of (low, medium, high)
- Due date: cannot be in the past (custom validator)

**Projects:**
- Name: 3-100 characters
- Description: max 500 characters
- Budget: must be positive if provided

**Tags:**
- Name: 1-50 characters, unique
- Color: valid hex color code (#RRGGBB)

**Comments:**
- Content: max 500 characters, required

---

## Technical Requirements

### Must Have:
- ✅ Type hints throughout all code
- ✅ Async route handlers where appropriate
- ✅ Proper error handling with appropriate HTTP status codes
- ✅ Auto-generated Swagger documentation
- ✅ Proper use of foreign keys and relationships
- ✅ Database indexes on frequently queried columns
- ✅ Pagination for list endpoints (skip/limit)
- ✅ Proper transaction handling with rollback
- ✅ Avoid N+1 query problems (use eager loading)

### Database Best Practices:
- Use UUIDs for primary keys
- Add created_at and updated_at timestamps
- Use ENUM types for status and priority
- Add appropriate indexes
- Use CASCADE deletes where appropriate
- Add database constraints

---

## Deliverables

Submit the following:

1. **Updated models.py** with all 5 new models
2. **Alembic migration files** (at least 4 migrations)
3. **Updated main.py** with all endpoints
4. **Pydantic schemas** for all models
5. **Testing commands** (curl or Postman collection)
6. **README updates** with:
   - Database schema diagram or description
   - Setup instructions
   - How to test the new features
   - Example API calls

---

## Evaluation Criteria

### Database Design (25%)
- Proper relationships (foreign keys, many-to-many)
- Appropriate data types
- Indexes on right columns
- Constraints and validations

### Migrations (15%)
- Clean migration files
- Migrations run without errors
- Proper up and down migrations
- Schema matches models

### CRUD Operations (20%)
- All endpoints working correctly
- Proper HTTP methods and status codes
- Error handling
- Input validation

### Complex Queries (20%)
- Efficient queries (no N+1 problems)
- Correct use of joins and aggregations
- Filtering and sorting work correctly
- Query performance

### Transactions (15%)
- Proper transaction handling
- Rollback works correctly
- Data consistency maintained
- Error handling in transactions

### Code Quality (5%)
- Type hints used
- Clean, readable code
- Proper naming conventions
- Comments where needed

---

## Bonus Points (Optional)

Implement any of these for extra credit:

1. **Soft Deletes** - Implement soft delete for tasks (is_deleted flag)
2. **Task History** - Track all changes to tasks
3. **Search** - Full-text search on task titles and descriptions
4. **Subtasks** - Support for subtasks (self-referential relationship)
5. **Task Dependencies** - Tasks can depend on other tasks
6. **Performance** - Add database query logging and optimize slow queries
7. **Testing** - Write pytest tests for critical endpoints
8. **Permissions** - Only project owner can delete project

---

## Hints & Resources

- Review existing User and UserProfile models for patterns
- Use SQLAlchemy relationships for joins
- Remember to use `db.commit()` and `db.refresh()`
- For transactions, use try/except with `db.rollback()`
- Use `joinedload()` to avoid N+1 queries
- Test each endpoint as you build it
- Check FastAPI docs for query parameters and filtering

---

## Common Challenges

**Challenge:** Many-to-many relationships  
**Tip:** Create association tables with explicit models

**Challenge:** Date validation  
**Tip:** Use Pydantic validators with `@validator` decorator

**Challenge:** Complex queries  
**Tip:** Use SQLAlchemy's `func` for aggregations and `join()` for relationships

**Challenge:** Transaction rollback  
**Tip:** Always use try/except blocks and call `db.rollback()` on errors

**Challenge:** N+1 queries  
**Tip:** Use `joinedload()` or `selectinload()` for related data

---

## Success Criteria

You've successfully completed this assignment when:

- ✅ All migrations run successfully
- ✅ All CRUD endpoints work correctly
- ✅ Complex queries return correct data
- ✅ Transactions handle errors with proper rollback
- ✅ No N+1 query problems
- ✅ API documentation is complete and accurate
- ✅ All validation rules are enforced
- ✅ Code is clean and well-organized

---

## Submission

Create a pull request or share your updated `sql_app` folder with:
- All code files
- Migration files
- Updated README
- Testing instructions

**Deadline:** [To be specified]

Good luck! 🚀
