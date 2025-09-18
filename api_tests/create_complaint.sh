ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNzU4MjI0NDg2fQ.af_LwxezX4MxgqvOx3rk8QqWz6Dxtg_kUG1bPDu4NUQ"

curl -X POST "http://127.0.0.1:8000/api/complaints" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '
{
  "title": "Noise Complaint",
  "description": "Loud music coming from next door",
  "department_code": "PD"
}'
