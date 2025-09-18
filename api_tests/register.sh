curl -X POST "http://127.0.0.1:8000/api/register" -H "Content-Type: application/json" -d '
{
  "name": "Test User",
  "phone": "1234567890",
  "email": "test@example.com",
  "password": "testpassword"
}'