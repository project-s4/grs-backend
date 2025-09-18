# Backend API Endpoints Documentation

This document outlines the request and response structures for the backend API endpoints.

## Base URL

All API endpoints are prefixed with `/api` unless otherwise specified.

## Authentication

Some endpoints require JWT-based authentication. After successful login, an `access_token` is returned, which should be included in the `Authorization` header of subsequent requests as a Bearer token (e.g., `Authorization: Bearer <access_token>`).

---

## 1. Complaints Endpoints

### `POST /api/complaints`

Creates a new complaint. This endpoint is used by citizens.

- **Request Body: `ComplaintCreate`**

  ```json
  {
    "title": "string",
    "description": "string",
    "transcript": "string | null",
    "language": "string | null",
    "translated_text": "string | null",
    "category": "string | null",
    "subcategory": "string | null",
    "department_code": "string",
    "source": "string (default: "web")",
    "complaint_metadata": "object | null"
  }
  ```

- **Response Body: `ComplaintResponse`**

  ```json
  {
    "id": "uuid",
    "reference_no": "string",
    "status": "string (e.g., "new", "in_progress")",
    "department_id": "uuid"
  }
  ```

---

## 2. AI Service Endpoints

### `POST /internal/ai/complaints`

Creates a new complaint via the AI service. This endpoint is for internal AI service use and is prefixed with `/internal`.

- **Request Body: `ComplaintCreate`**

  (Same as `POST /api/complaints`)

  ```json
  {
    "title": "string",
    "description": "string",
    "transcript": "string | null",
    "language": "string | null",
    "translated_text": "string | null",
    "category": "string | null",
    "subcategory": "string | null",
    "department_code": "string",
    "source": "string (default: "web")",
    "complaint_metadata": "object | null"
  }
  ```

- **Response Body: `ComplaintResponse`**

  (Same as `POST /api/complaints`)

  ```json
  {
    "id": "uuid",
    "reference_no": "string",
    "status": "string (e.g., "new", "in_progress")",
    "department_id": "uuid"
  }
  ```

---

## 3. Authentication Endpoints

### `POST /api/register`

Registers a new user.

- **Request Body: `UserCreate`**

  ```json
  {
    "name": "string",
    "phone": "string",
    "email": "string (email format) | null",
    "password": "string",
    "role": "string (enum: "citizen", "admin", "department", default: "citizen")",
    "department_id": "uuid | null"
  }
  ```

- **Response Body: `UserResponse`**

  ```json
  {
    "id": "uuid",
    "name": "string",
    "phone": "string",
    "email": "string (email format) | null",
    "role": "string (enum: "citizen", "admin", "department")"
  }
  ```

### `POST /api/login`

Authenticates a user and returns an access token.

- **Request Body: Form Data (`application/x-www-form-urlencoded`)**

  ```
  username: string (user's email)
  password: string
  ```

- **Response Body:**

  ```json
  {
    "access_token": "string",
    "token_type": "string (default: "bearer")"
  }
  ```

---

## 4. Departments Endpoints

### `POST /api/departments`

Creates a new department.

- **Request Body: `DepartmentCreate`**

  ```json
  {
    "name": "string",
    "code": "string",
    "parent_department_id": "uuid | null"
  }
  ```

- **Response Body: `DepartmentResponse`**

  ```json
  {
    "id": "uuid",
    "name": "string",
    "code": "string"
  }
  ```
