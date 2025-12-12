#!/bin/bash

# Test Document Generation Flow End-to-End

echo "=== Document Generation Flow Test ==="
echo ""

# Get auth token
echo "1. Logging in..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "hr@talent.com", "password": "hr123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "Token obtained: ${TOKEN:0:20}..."
echo ""

# Start session
echo "2. Starting new document session..."
SESSION_RESP=$(curl -s -X POST http://localhost:8000/api/v1/documents/agent/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{}')

echo "$SESSION_RESP" | python3 -m json.tool
SESSION_ID=$(echo "$SESSION_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin)['session_id'])")
echo "Session ID: $SESSION_ID"
echo ""

# Select template
echo "3. Selecting Offer Letter template..."
curl -s -X POST http://localhost:8000/api/v1/documents/agent/template \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"session_id\": \"$SESSION_ID\", \"template_id\": 1}" | python3 -m json.tool
echo ""

# Choose manual entry
echo "4. Choosing manual entry method..."
curl -s -X POST http://localhost:8000/api/v1/documents/agent/input-method \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"session_id\": \"$SESSION_ID\", \"method\": \"manual_entry\"}" | python3 -m json.tool
echo ""

# Submit fields one by one
echo "5. Submitting field 1: employee_name = 'John Smith'..."
curl -s -X POST http://localhost:8000/api/v1/documents/agent/manual-field \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"session_id\": \"$SESSION_ID\", \"field_name\": \"employee_name\", \"field_value\": \"John Smith\"}" | python3 -m json.tool
echo ""

echo "6. Submitting field 2: designation = 'Senior Software Engineer'..."
curl -s -X POST http://localhost:8000/api/v1/documents/agent/manual-field \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"session_id\": \"$SESSION_ID\", \"field_name\": \"designation\", \"field_value\": \"Senior Software Engineer\"}" | python3 -m json.tool
echo ""

echo "7. Submitting field 3: department = 'Engineering'..."
curl -s -X POST http://localhost:8000/api/v1/documents/agent/manual-field \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"session_id\": \"$SESSION_ID\", \"field_name\": \"department\", \"field_value\": \"Engineering\"}" | python3 -m json.tool
echo ""

echo "8. Submitting field 4: joining_date = '2025-01-15'..."
curl -s -X POST http://localhost:8000/api/v1/documents/agent/manual-field \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"session_id\": \"$SESSION_ID\", \"field_name\": \"joining_date\", \"field_value\": \"2025-01-15\"}" | python3 -m json.tool
echo ""

echo "9. Submitting field 5: salary = '120000'..."
curl -s -X POST http://localhost:8000/api/v1/documents/agent/manual-field \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"session_id\": \"$SESSION_ID\", \"field_name\": \"salary\", \"field_value\": \"120000\"}" | python3 -m json.tool
echo ""

echo "10. Submitting field 6: location = 'New York Office'..."
curl -s -X POST http://localhost:8000/api/v1/documents/agent/manual-field \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"session_id\": \"$SESSION_ID\", \"field_name\": \"location\", \"field_value\": \"New York Office\"}" | python3 -m json.tool
echo ""

# Preview
echo "11. Generating preview..."
PREVIEW_RESP=$(curl -s -X POST http://localhost:8000/api/v1/documents/agent/preview \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"session_id\": \"$SESSION_ID\"}")

echo "$PREVIEW_RESP" | python3 -c "import sys, json; data=json.load(sys.stdin); print('All fields valid:', data.get('all_fields_valid')); print('Validation errors:', data.get('validation_errors')); print('Collected data:', data.get('collected_data'))"
echo ""

# Generate document
echo "12. Generating PDF document..."
GEN_RESP=$(curl -s -X POST http://localhost:8000/api/v1/documents/agent/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"session_id\": \"$SESSION_ID\", \"format\": \"pdf\"}")

echo "$GEN_RESP" | python3 -m json.tool
DOC_ID=$(echo "$GEN_RESP" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('document_ids', [None])[0] if data.get('document_ids') else 'None')")
echo ""
echo "Document ID: $DOC_ID"
echo ""

# Check backend logs for debug output
echo "13. Checking backend debug logs..."
tail -100 /home/amramesh/wsl/Talent_Connect/backend/backend.log | grep "🔍 DEBUG"
echo ""

echo "=== Test Complete ==="
