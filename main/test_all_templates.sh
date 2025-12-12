#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║    Testing All Document Templates - Data Persistence Check    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:6173"

# Test template data
declare -A TEMPLATE_TESTS=(
    # Template ID: Fields data
    ["1"]="employee_name=John Smith|designation=Senior Engineer|department=Engineering|joining_date=2025-01-15|salary=120000|location=New York"
    ["2"]="employee_name=Jane Doe|employee_code=EMP001|designation=Software Developer|joining_date=2023-01-01|last_working_date=2025-01-15"
    ["3"]="employee_name=Bob Johnson|employee_code=EMP002|designation=Product Manager|last_working_date=2025-02-01"
    ["7"]="employee_name=Alice Brown|employee_code=EMP003|designation=Team Lead|joining_date=2024-01-01|confirmation_date=2024-07-01"
)

declare -A TEMPLATE_NAMES=(
    ["1"]="Offer Letter"
    ["2"]="Experience Letter"
    ["3"]="Relieving Letter"
    ["7"]="Confirmation Letter"
)

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

test_template() {
    local template_id=$1
    local template_name=$2
    local fields_data=$3
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Testing: $template_name (ID: $template_id)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Login
    echo "1. Logging in..."
    LOGIN_RESP=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/demo-login" \
        -H "Content-Type: application/json" \
        -d '{"email": "hr@talent.com"}')
    
    TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('access_token', ''))" 2>/dev/null)
    
    if [ -z "$TOKEN" ]; then
        echo -e "${RED}✗ Login failed${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ Logged in${NC}"
    
    # Start session
    echo "2. Starting session..."
    SESSION_RESP=$(curl -s -X POST "$BACKEND_URL/api/v1/documents/agent/start" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{}')
    
    SESSION_ID=$(echo "$SESSION_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin)['session_id'])" 2>/dev/null)
    
    if [ -z "$SESSION_ID" ]; then
        echo -e "${RED}✗ Session creation failed${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ Session created: ${SESSION_ID:0:8}...${NC}"
    
    # Select template
    echo "3. Selecting template..."
    curl -s -X POST "$BACKEND_URL/api/v1/documents/agent/select-template" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d "{\"session_id\": \"$SESSION_ID\", \"template_id\": $template_id}" > /dev/null
    
    # Choose manual entry
    curl -s -X POST "$BACKEND_URL/api/v1/documents/agent/input-method" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d "{\"session_id\": \"$SESSION_ID\", \"method\": \"manual_entry\"}" > /dev/null
    
    echo -e "${GREEN}✓ Template selected and manual entry mode set${NC}"
    
    # Submit fields
    echo "4. Submitting fields..."
    IFS='|' read -ra FIELDS <<< "$fields_data"
    local field_count=${#FIELDS[@]}
    local submitted_count=0
    
    for field in "${FIELDS[@]}"; do
        IFS='=' read -r field_name field_value <<< "$field"
        
        FIELD_RESP=$(curl -s -X POST "$BACKEND_URL/api/v1/documents/agent/manual-field" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $TOKEN" \
            -d "{\"session_id\": \"$SESSION_ID\", \"field_name\": \"$field_name\", \"field_value\": \"$field_value\"}")
        
        # Check for validation error
        HAS_ERROR=$(echo "$FIELD_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('validation_error', False))" 2>/dev/null)
        
        if [ "$HAS_ERROR" == "True" ]; then
            echo -e "${RED}   ✗ $field_name: validation failed${NC}"
        else
            echo -e "${GREEN}   ✓ $field_name: $field_value${NC}"
            ((submitted_count++))
        fi
        
        sleep 0.2
    done
    
    echo "   Submitted $submitted_count/$field_count fields"
    
    # Check data persistence via preview
    echo "5. Checking data persistence (preview)..."
    PREVIEW_RESP=$(curl -s -X POST "$BACKEND_URL/api/v1/documents/agent/preview" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d "{\"session_id\": \"$SESSION_ID\"}")
    
    COLLECTED_DATA=$(echo "$PREVIEW_RESP" | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data.get('collected_data', {})))" 2>/dev/null)
    FIELD_COUNT=$(echo "$COLLECTED_DATA" | python3 -c "import sys, json; print(len(json.loads(sys.stdin)))" 2>/dev/null)
    
    echo "   Collected data has $FIELD_COUNT fields"
    
    if [ "$FIELD_COUNT" -eq "$submitted_count" ]; then
        echo -e "${GREEN}✓ Data persistence verified - all $FIELD_COUNT fields retained${NC}"
        PERSISTENCE_OK=1
    else
        echo -e "${RED}✗ Data persistence FAILED - expected $submitted_count, got $FIELD_COUNT${NC}"
        echo "   Collected data: $COLLECTED_DATA"
        PERSISTENCE_OK=0
    fi
    
    # Generate document
    echo "6. Generating document..."
    GEN_RESP=$(curl -s -X POST "$BACKEND_URL/api/v1/documents/agent/generate" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d "{\"session_id\": \"$SESSION_ID\", \"format\": \"pdf\"}")
    
    DOC_IDS=$(echo "$GEN_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('document_ids', []))" 2>/dev/null)
    
    if [[ "$DOC_IDS" == *"["* ]]; then
        echo -e "${GREEN}✓ Document generated successfully${NC}"
        GENERATION_OK=1
    else
        echo -e "${RED}✗ Document generation failed${NC}"
        GENERATION_OK=0
    fi
    
    # Final result
    echo ""
    if [ "$PERSISTENCE_OK" -eq 1 ] && [ "$GENERATION_OK" -eq 1 ]; then
        echo -e "${GREEN}✅ PASSED: $template_name${NC}"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}❌ FAILED: $template_name${NC}"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    echo ""
    return 0
}

# Run tests
echo "Starting tests..."
echo ""

for template_id in "${!TEMPLATE_TESTS[@]}"; do
    test_template "$template_id" "${TEMPLATE_NAMES[$template_id]}" "${TEMPLATE_TESTS[$template_id]}"
    sleep 1
done

# Summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                        Test Summary                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Total Tests:  $TOTAL_TESTS"
echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed:       ${RED}$FAILED_TESTS${NC}"
echo ""

if [ "$FAILED_TESTS" -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Data persistence is working correctly.${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Check the output above for details.${NC}"
    exit 1
fi
