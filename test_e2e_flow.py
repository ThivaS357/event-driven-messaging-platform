import json
from bson.objectid import ObjectId
from unittest.mock import MagicMock

def test_e2e_webhook_to_campaign_to_status(client, mocker):
    """
    End-to-end test for the following flow:
    1. An event is ingested that triggers a campaign.
    2. The campaign runner sends a message via a mocked Twilio client.
    3. A status callback is received for the message.
    """
    # --- 1. Setup: Seed the mock database and mock Twilio ---

    # Import db inside the test to ensure it's the patched version
    from app.data.database import mongo_db as db

    db.users.delete_many({})
    db.templates.delete_many({})
    db.campaigns.delete_many({})
    db.subscriptions.delete_many({})
    db.delivery_receipts.delete_many({})

    # Seed data
    user_id = "+15550001111"
    template_id = str(ObjectId())
    campaign_id = str(ObjectId())
    
    db.users.insert_one({"_id": user_id, "id": user_id, "name": "E2E Tester", "consent_state": "STARTED", "attributes": {"name": "E2E"}})
    db.templates.insert_one({"_id": ObjectId(template_id), "content": "Hello {{name}}"})
    db.subscriptions.insert_one({"user_id": user_id, "topic": "PROMOTIONS"})
    db.campaigns.insert_one({
        "_id": ObjectId(campaign_id),
        "topic": "PROMOTIONS",
        "template_id": template_id,
        "status": "scheduled"
    })

    # Mock the Twilio client in the campaign_runner service
    mock_twilio_client = MagicMock()
    mock_message = MagicMock()
    mock_message.sid = "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    mock_twilio_client.messages.create.return_value = mock_message
    mocker.patch('app.services.campaign_runner.client', mock_twilio_client)

    # --- 2. Trigger: Ingest an event that starts the campaign ---

    event_data = {
        "event_type": "promotion_trigger",
        "segment_rule": {"topic": "PROMOTIONS"}
    }
    # Create a file-like object for the request
    from io import BytesIO
    jsonl_content = json.dumps(event_data).encode('utf-8')
    
    response = client.post(
        '/api/v1/ingestions/events',
        data={'file': (BytesIO(jsonl_content), 'test.jsonl')},
        content_type='multipart/form-data'
    )

    assert response.status_code == 200
    assert response.json['campaigns_triggered'] == 1

    # --- 3. Verification (Part 1): Check if Twilio was called ---

    mock_twilio_client.messages.create.assert_called_once()
    call_args = mock_twilio_client.messages.create.call_args
    assert call_args.kwargs['to'] == f"whatsapp:{user_id}"
    # The content variables are now a JSON string
    assert '"1": "Hello E2E"' in call_args.kwargs['content_variables']

    # --- 4. Trigger (Part 2): Simulate Twilio status callback ---

    status_payload = {
        "MessageSid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "MessageStatus": "delivered"
    }
    response = client.post('/twilio/status', data=status_payload)
    assert response.status_code == 200

    # --- 5. Verification (Part 2): Check if the status was logged ---

    receipt = db.delivery_receipts.find_one({"message_sid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"})
    assert receipt is not None
    assert receipt['status'] == 'delivered'
