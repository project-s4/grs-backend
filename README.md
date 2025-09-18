# Grievance Redressal Backend

This repository contains the backend for a Grievance Redressal System, built using FastAPI, PostgreSQL, and JWT-based authentication. It provides a robust API for citizens, departments, administrators, and an AI service to manage and process grievances efficiently.

## Features

*   **FastAPI:** High-performance, easy-to-use web framework for building APIs.
*   **PostgreSQL:** Reliable and powerful relational database.
*   **SQLAlchemy ORM:** Pythonic way to interact with the database.
*   **JWT Authentication:** Secure token-based authentication for all API interactions.
*   **Alembic:** Database migration tool for managing schema changes.
*   **Modular Design:** Well-organized project structure for maintainability and scalability.
*   **Dedicated APIs:** Endpoints for user authentication, department management, complaint submission (citizen & AI), and administrative tasks.

## Getting Started

Follow these steps to get the project up and running on your local machine.

### Prerequisites

Ensure you have the following installed:

*   [Docker](https://docs.docker.com/get-docker/) (for PostgreSQL database)
*   [Python 3.8+](https://www.python.org/downloads/)
*   [pip](https://pip.pypa.io/en/stable/installation/) (Python package installer)

### Quick Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/project-s4/grs-backend.git
    cd grs-backend
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Start the PostgreSQL database using Docker Compose:**
    ```bash
    docker compose up -d
    ```

4.  **Run database migrations:**
    ```bash
    alembic upgrade head
    ```

5.  **Start the FastAPI application:**
    ```bash
    uvicorn app.main:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`.

For more detailed setup instructions, including troubleshooting and environment configuration, please refer to the [Setup Guide](./docs/setup.md).

## API Endpoints

The backend exposes several API endpoints for different functionalities:

*   **Authentication:** Register users, log in, and obtain JWT tokens. See [Authentication Documentation](./docs/authentication.md).
*   **Departments:** Manage departmental information. See [Departments Documentation](./docs/departments.md).
*   **Complaints:** Submit and manage grievances. See [Complaints Documentation](./docs/complaints.md).
*   **AI Service:** Internal endpoint for AI-driven complaint submission. See [AI Service Documentation](./docs/ai_service.md).

## Database

Information about the database schema, models, and Alembic migrations can be found in the [Database Documentation](./docs/database.md).

## Full Documentation

For a complete overview of the project, including detailed API specifications, setup guides, and architectural decisions, please visit the [Full Documentation](./docs/README.md).