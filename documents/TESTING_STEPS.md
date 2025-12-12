# Document Generation Testing Steps

## System Status
✅ Backend: Running on http://localhost:8000  
✅ Frontend: Running on http://localhost:6173  
✅ Debug logging enabled

## Test Steps

### 1. Open Browser
Navigate to: **http://localhost:6173**

### 2. Login
- Email: `hr@talent.com`
- Password: `hr123`

### 3. Navigate to Document Agent
- Click "Documents" in the sidebar
- Click "Agent" tab

### 4. Start Document Generation
- Click on "Offer Letter" template
- Click "Manual Entry" button

### 5. Fill Fields **ONE BY ONE** (Wait for each response!)

**Field 1: Employee Name**
- Enter: `John Smith`
- Press Send
- ✅ Wait for "✓ Got it!" message
- ✅ Check sidebar shows ✓ for employee_name

**Field 2: Designation**  
- Enter: `Senior Software Engineer`
- Press Send
- ✅ Wait for "✓ Got it!" message
- ✅ Check sidebar shows ✓ for designation

**Field 3: Department**
- Enter: `Engineering`
- Press Send
- ✅ Wait for "✓ Got it!" message
- ✅ Check sidebar shows ✓ for department

**Field 4: Joining Date**
- Enter: `2025-01-15`
- Press Send
- ✅ Wait for "✓ Got it!" message
- ✅ Check sidebar shows ✓ for joining_date

**Field 5: Salary**
- Enter: `120000`
- Press Send
- ✅ Wait for "✓ Got it!" message
- ✅ Check sidebar shows ✓ for salary

**Field 6: Location**
- Enter: `New York Office`
- Press Send
- ✅ Wait for "✓ Got it!" message
- ✅ Check sidebar shows ✓ for location

### 6. Preview Document
- ✅ "Preview Document" button should appear
- Click "Preview Document"
- ✅ Modal should open showing the document preview
- ✅ Check that all fields are filled in the preview (not [PLACEHOLDERS])

### 7. Generate Document
- Select format: PDF or DOCX
- Click "Generate PDF" (or Generate DOCX)
- ✅ Wait for success message
- ✅ Document should appear in library

## Debug Logs to Watch

While testing, the backend logs will show:
```
🔍 DEBUG process_manual_field: field_name=employee_name, field_value=John Smith
🔍 DEBUG current context: {...}
🔍 DEBUG validation result: is_valid=True, error=None
🔍 DEBUG ctx before update: {...}
🔍 DEBUG ctx after update: {...}
🔍 DEBUG manual_data now has: {'employee_name': 'John Smith'}
🔍 DEBUG filled_fields: ['employee_name'], remaining: [...]
```

## Expected Behavior

### ✅ Success Indicators:
1. Each field submission shows ✓ checkmark
2. Sidebar updates with ✓ for each filled field
3. Preview shows actual values (not placeholders)
4. Generate creates document with all data filled

### ❌ Failure Indicators:
1. Validation errors (❌) for invalid input
2. Preview shows [PLACEHOLDERS] instead of values
3. Generated PDF has empty fields

## Troubleshooting

### If preview shows placeholders:
1. Check backend logs for "🔍 DEBUG manual_data now has:"
2. Verify all 6 fields are in the manual_data dict
3. If not, some fields weren't submitted - go back and re-fill

### If validation fails:
1. Look for "❌ Validation Error" message
2. Read the hint provided
3. Re-enter the field with correct format

### If nothing works:
1. Check backend logs: `tail -100 /home/amramesh/wsl/Talent_Connect/backend/backend.log`
2. Look for errors or debug messages
3. Restart both backend and frontend if needed

## Commands to Monitor

**Watch backend logs in real-time:**
```bash
tail -f /home/amramesh/wsl/Talent_Connect/backend/backend.log | grep "🔍 DEBUG"
```

**Check if services are running:**
```bash
# Backend
curl http://localhost:8000/docs

# Frontend  
curl http://localhost:6173
```

## After Testing

Share the results:
- Did preview show all values correctly?
- Was the generated PDF filled with data?
- Were there any errors in the logs?
