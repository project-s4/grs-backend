# Complaints API

This section describes the API endpoints related to managing complaints.

## Endpoints

### 1. Create a New Complaint

*   **URL:** `/api/complaints`
*   **Method:** `POST`
*   **Description:** Allows a citizen to create a new complaint. Requires authentication.
*   **Request Body (application/json):**

    ```json
    {
      "title": "Noise Complaint",
      "description": "Loud music coming from next door",
      "transcript": "Optional transcript of a call",
      "language": "en",
      "translated_text": "Optional translated text",
      "category": "Public Order",
      "subcategory": "Noise",
      "department_code": "PD",
      "source": "web",
      "complaint_metadata": {"key": "value"}
    }
    ```

*   **Response (200 OK, application/json):**

    ```json
    {
      "id": "uuid",
      "reference_no": "string",
      "status": "new",
      "department_id": "uuid"
    }
    ```

## Models

### `ComplaintCreate` Schema

```python
from pydantic import BaseModel
from typing import Optional, Dict
import uuid

class ComplaintCreate(BaseModel):
    title: str
    description: str
    transcript: Optional[str] = None
    language: Optional[str] = None
    translated_text: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    department_code: str
    source: str = "web"
    complaint_metadata: Optional[Dict] = None
```

### `ComplaintResponse` Schema

```python
from pydantic import BaseModel
import uuid

class ComplaintResponse(BaseModel):
    id: uuid.UUID
    reference_no: str
    status: str
    department_id: uuid.UUID
```
