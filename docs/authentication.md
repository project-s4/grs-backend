# Authentication

This backend uses JWT (JSON Web Token) for authentication. Users can register and then log in to obtain an access token, which must be included in subsequent requests to protected endpoints.

## Endpoints

### 1. Register a New User

*   **URL:** `/api/register`
*   **Method:** `POST`
*   **Description:** Creates a new user account.
*   **Request Body (application/json):**

    ```json
    {
      "name": "string",
      "phone": "string",
      "email": "user@example.com",
      "password": "string",
      "role": "citizen" // or "admin", "department"
    }
    ```

*   **Response (200 OK, application/json):**

    ```json
    {
      "id": "uuid",
      "name": "string",
      "phone": "string",
      "email": "user@example.com",
      "role": "citizen"
    }
    ```

### 2. User Login

*   **URL:** `/api/login`
*   **Method:** `POST`
*   **Description:** Authenticates a user and returns an access token.
*   **Request Body (application/x-www-form-urlencoded):**

    ```
    username=user@example.com&password=string
    ```

*   **Response (200 OK, application/json):**

    ```json
    {
      "access_token": "your_jwt_token_here",
      "token_type": "bearer"
    }
    ```

## Using the Access Token

Once you have an `access_token`, include it in the `Authorization` header of your requests to protected endpoints:

```
Authorization: Bearer <YOUR_ACCESS_TOKEN>
```

**Example (using curl):**

```bash
ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
curl -X GET "http://127.0.0.1:8000/protected-endpoint" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```
