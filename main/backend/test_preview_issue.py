#!/usr/bin/env python3
"""
Test script to diagnose the preview issue - traces the complete flow
"""
import asyncio
import httpx
import json
from pathlib import Path

API_BASE = "http://localhost:8000/api/v1"
DOCS_API_BASE = "http://localhost:8000"

async def test_preview_flow():
    async with httpx.AsyncClient() as client:
        print("=" * 80)
        print("TESTING PREVIEW FLOW")
        print("=" * 80)
        
        # 1. Login
        print("\n1️⃣  LOGIN")
        login_response = await client.post(
            f"{API_BASE}/auth/login",
            json={"email": "hr@dhl.com", "password": "password123"}
        )
        print(f"Status: {login_response.status_code}")
        login_data = login_response.json()
        token = login_data.get("token")
        print(f"Token obtained: {token[:30]}...")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Start conversation
        print("\n2️⃣  START CONVERSATION")
        start_response = await client.post(
            f"{DOCS_API_BASE}/documents/agent/start",
            headers=headers,
            json={}
        )
        print(f"Status: {start_response.status_code}")
        start_data = start_response.json()
        session_id = start_data.get("session_id")
        print(f"Session ID: {session_id}")
        templates = start_data.get("templates", [])
        print(f"Templates available: {len(templates)}")
        for t in templates[:3]:
            print(f"  - {t.get('name')}")
        
        # Find Offer Letter template
        offer_letter_template = None
        for t in templates:
            if "offer" in t.get("name", "").lower():
                offer_letter_template = t
                break
        
        if not offer_letter_template:
            print("❌ No Offer Letter template found!")
            return
        
        template_id = offer_letter_template.get("id")
        print(f"\nSelected template: {offer_letter_template.get('name')} (ID: {template_id})")
        
        # 3. Select template
        print("\n3️⃣  SELECT TEMPLATE")
        select_response = await client.post(
            f"{DOCS_API_BASE}/documents/agent/select-template",
            headers=headers,
            json={"session_id": session_id, "template_id": template_id}
        )
        print(f"Status: {select_response.status_code}")
        select_data = select_response.json()
        print(f"Message: {select_data.get('message', '')[:100]}")
        
        # 4. Select input method (manual)
        print("\n4️⃣  SELECT INPUT METHOD (MANUAL)")
        input_method_response = await client.post(
            f"{DOCS_API_BASE}/documents/agent/input-method",
            headers=headers,
            json={"session_id": session_id, "method": "manual"}
        )
        print(f"Status: {input_method_response.status_code}")
        input_method_data = input_method_response.json()
        print(f"Message: {input_method_data.get('message', '')[:100]}")
        
        # 5. Submit manual fields
        print("\n5️⃣  SUBMIT MANUAL FIELDS")
        test_data = {
            "session_id": session_id,
            "field_name": "candidate_name",
            "field_value": "Sarah Johnson"
        }
        
        fields_to_submit = [
            ("candidate_name", "Sarah Johnson"),
            ("position", "Senior Software Engineer"),
            ("joining_date", "2025-02-01"),
            ("salary", "2500000")
        ]
        
        for field_name, field_value in fields_to_submit:
            field_response = await client.post(
                f"{DOCS_API_BASE}/documents/agent/manual-field",
                headers=headers,
                json={
                    "session_id": session_id,
                    "field_name": field_name,
                    "field_value": field_value
                }
            )
            print(f"  {field_name}: Status {field_response.status_code}")
            if field_response.status_code != 200:
                print(f"    Error: {field_response.text}")
        
        # 6. GET PREVIEW - THIS IS THE KEY TEST
        print("\n6️⃣  REQUEST PREVIEW")
        print(f"Session ID being sent: {session_id}")
        
        preview_response = await client.post(
            f"{DOCS_API_BASE}/documents/agent/preview",
            headers=headers,
            json={"session_id": session_id}
        )
        
        print(f"Status: {preview_response.status_code}")
        print(f"Response headers: {dict(preview_response.headers)}")
        
        preview_data = preview_response.json()
        print(f"\nResponse keys: {list(preview_data.keys())}")
        
        # Check validation errors
        validation_errors = preview_data.get("validation_errors")
        print(f"Validation errors: {validation_errors}")
        
        # Check all fields valid
        all_valid = preview_data.get("all_fields_valid")
        print(f"All fields valid: {all_valid}")
        
        # Check collected data
        collected_data = preview_data.get("collected_data")
        print(f"\nCollected data keys: {list(collected_data.keys())}")
        print(f"Collected data: {json.dumps(collected_data, indent=2)}")
        
        # Check preview HTML
        preview_html = preview_data.get("preview_html", "")
        print(f"\nPreview HTML length: {len(preview_html)}")
        print(f"Preview HTML first 500 chars:\n{preview_html[:500]}")
        
        # Check if filled values appear in HTML
        print("\n🔍 CHECKING IF FILLED VALUES APPEAR IN HTML:")
        test_values = ["Sarah Johnson", "Senior Software Engineer", "2025-02-01", "2500000"]
        for value in test_values:
            if value in preview_html:
                print(f"  ✅ '{value}' FOUND in preview HTML")
            else:
                print(f"  ❌ '{value}' NOT FOUND in preview HTML")
        
        # Check if placeholders still exist
        print("\n🔍 CHECKING FOR UNFILLED PLACEHOLDERS:")
        placeholders = ["[Employee Name]", "[Designation]", "[Date of Joining]", "[CTC]"]
        for placeholder in placeholders:
            if placeholder in preview_html:
                print(f"  ⚠️  UNFILLED: '{placeholder}' still in HTML")
            else:
                print(f"  ✅ FILLED: '{placeholder}' not in HTML")
        
        # Save HTML to file for inspection
        html_file = Path("/tmp/preview_debug.html")
        html_file.write_text(preview_html)
        print(f"\n📄 Full preview HTML saved to: {html_file}")

if __name__ == "__main__":
    print("\n🚀 Starting preview flow test...")
    asyncio.run(test_preview_flow())
    print("\n✅ Test complete!")
