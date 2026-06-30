import json
from app import app

def test_valid_submission():
    """Test valid text submission."""
    client = app.test_client()
    response = client.post(
        '/submit',
        data=json.dumps({'text': 'This is a sample text for testing.'}),
        content_type='application/json',
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'result' in data
    assert 'confidence' in data['result']
    print('Test valid submission: PASSED')


def test_missing_text_field():
    """Test submission with missing text field."""
    client = app.test_client()
    response = client.post(
        '/submit',
        data=json.dumps({}),
        content_type='application/json',
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'Validation error'
    print('Test missing text field: PASSED')


def test_empty_text():
    """Test submission with empty text."""
    client = app.test_client()
    response = client.post(
        '/submit',
        data=json.dumps({'text': '   '}),
        content_type='application/json',
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'Validation error'
    print('Test empty text: PASSED')


def test_invalid_json():
    """Test submission with invalid JSON."""
    client = app.test_client()
    response = client.post(
        '/submit',
        data='not valid json',
        content_type='application/json',
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'Validation error'
    print('Test invalid JSON: PASSED')


def test_text_not_string():
    """Test submission with non-string text field."""
    client = app.test_client()
    response = client.post(
        '/submit',
        data=json.dumps({'text': 12345}),
        content_type='application/json',
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'Validation error'
    print('Test text not string: PASSED')


def test_health_check():
    """Test health check endpoint."""
    client = app.test_client()
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    print('Test health check: PASSED')


def test_content_normalization():
    """Test that content is properly normalized."""
    client = app.test_client()
    messy_text = '  Hello   world  \n\n\n  with    spaces  &amp;  entities  '
    response = client.post(
        '/submit',
        data=json.dumps({'text': messy_text}),
        content_type='application/json',
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    print('Test content normalization: PASSED')


def test_response_structure():
    """Test response contains required fields."""
    client = app.test_client()
    response = client.post(
        '/submit',
        data=json.dumps({'text': 'Test content for structure validation.'}),
        content_type='application/json',
    )
    assert response.status_code == 200
    data = response.get_json()
    assert 'success' in data
    assert 'result' in data
    
    assert 'content_id' in data['result']
    assert 'label' in data['result']
    assert 'confidence' in data['result']
    assert 'reasoning' in data['result']
    assert 0.0 <= data['result']['confidence'] <= 1.0
    print('Test response structure: PASSED')


if __name__ == '__main__':
    test_valid_submission()
    test_missing_text_field()
    test_empty_text()
    test_invalid_json()
    test_text_not_string()
    test_health_check()
    test_content_normalization()
    test_response_structure()
    print('\nAll tests passed!')
