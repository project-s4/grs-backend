# Departments API

This section describes the API endpoints related to managing departments.

## Endpoints

### 1. Create a New Department

*   **URL:** `/api/departments`
*   **Method:** `POST`
*   **Description:** Creates a new department. Requires authentication.
*   **Request Body (application/json):**

    ```json
    {
      "name": "Police Department",
      "code": "PD",
      "parent_department_id": null // Optional: UUID of a parent department
    }
    ```

*   **Response (200 OK, application/json):**

    ```json
    {
      "id": "uuid",
      "name": "Police Department",
      "code": "PD"
    }
    ```

## Models

### `DepartmentCreate` Schema

```python
from pydantic import BaseModel
from typing import Optional
import uuid

class DepartmentCreate(BaseModel):
    name: str
    code: str
    parent_department_id: Optional[uuid.UUID] = None
```

### `DepartmentResponse` Schema

```python
from pydantic import BaseModel
import uuid

class DepartmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str
```
