import os
import sys
import json
import tempfile
import shutil

sys.path.insert(0, '/mnt/project')

from appeal_validator import validate_appeal_form
from appeal_manager import (
    update_content_status,
    check_appeal_eligibility,
    create_appeal,
    get_content_status,
)
from reviewer_dashboard import (
    get_pending_appeals,
    get_appeal_detail,
    format_appeal_for_reviewer,
)
from decision_processor import (
    submit_decision,
    get_appeal_statistics,
)


def setup_test_environment():
    """Create temporary directory for test files."""
    original_dir = os.getcwd()
    test_dir = tempfile.mkdtemp(prefix='appeal_test_')
    os.chdir(test_dir)
    return test_dir, original_dir


def cleanup_test_environment(test_dir, original_dir):
    """Clean up test files."""
    os.chdir(original_dir)
    shutil.rmtree(test_dir)


def test_appeal_form_validation():
    """Test appeal form validation."""
    print("[TEST 1] Appeal Form Validation")
    
    valid_form = {
        'email': 'creator@example.com',
        'reasoning': 'This is a detailed explanation of why the classification is incorrect. I spent considerable time writing this content.',
        'writing_date': '2024-06-15',
        'process_duration_hours': 2.5,
        'writing_process': 'original composition',
        'native_language': 'English',
        'ai_assisted': False,
        'additional_context': 'Additional information about the writing process',
    }
    
    is_valid, errors = validate_appeal_form(valid_form)
    assert is_valid == True, f"Valid form should pass: {errors}"
    print("✓ Valid form passes validation")
    
    invalid_form = {
        'email': 'invalid-email',
        'reasoning': 'short',
        'writing_date': '2024/06/15',
        'process_duration_hours': -1,
        'writing_process': 'invalid process',
        'native_language': 'E',
        'ai_assisted': 'not a boolean',
    }
    
    is_valid, errors = validate_appeal_form(invalid_form)
    assert is_valid == False, "Invalid form should fail"
    assert 'email' in errors, "Email error should be present"
    assert 'reasoning' in errors, "Reasoning error should be present"
    assert 'writing_date' in errors, "Date error should be present"
    print("✓ Invalid form correctly rejects all errors")


def test_content_status_tracking():
    """Test content status tracking."""
    print("\n[TEST 2] Content Status Tracking")
    
    test_dir, original_dir = setup_test_environment()
    
    try:
        classification_result = {
            'label': 'Your text is Human written',
            'confidence': 0.12,
            'signals': {},
        }
        
        success = update_content_status('CTN-2024-06-15-TEST', classification_result)
        assert success == True, "Should update content status"
        print("✓ Content status successfully updated")
        
        status = get_content_status('CTN-2024-06-15-TEST')
        assert status is not None, "Status should be retrievable"
        assert status['status'] == 'classified', "Status should be 'classified'"
        assert status['label'] == 'Your text is Human written', "Label should match"
        print("✓ Content status correctly retrieved")
        
    finally:
        cleanup_test_environment(test_dir, original_dir)


def test_appeal_eligibility():
    """Test appeal eligibility checking."""
    print("\n[TEST 3] Appeal Eligibility Checking")
    
    test_dir, original_dir = setup_test_environment()
    
    try:
        classification_result = {
            'label': 'Your text is Human written',
            'confidence': 0.12,
            'signals': {},
        }
        update_content_status('CTN-2024-06-15-TEST', classification_result)
        
        eligible, reason = check_appeal_eligibility('CTN-2024-06-15-TEST')
        assert eligible == True, "Fresh content should be eligible"
        print("✓ Fresh content is eligible for appeal")
        
        eligible, reason = check_appeal_eligibility('CTN-NONEXISTENT')
        assert eligible == False, "Nonexistent content should not be eligible"
        assert 'not found' in reason, "Reason should indicate content not found"
        print("✓ Nonexistent content correctly rejected")
        
    finally:
        cleanup_test_environment(test_dir, original_dir)


def test_appeal_creation():
    """Test appeal creation and logging."""
    print("\n[TEST 4] Appeal Creation and Logging")
    
    test_dir, original_dir = setup_test_environment()
    
    try:
        classification_result = {
            'label': 'Your text is Likely AI-generated',
            'confidence': 0.75,
            'signals': {
                'llm_judgment': {'score': 0.8, 'reasoning': 'test'},
                'stylometry': {'score': 0.7, 'reasoning': 'test', 'subscores': {}},
                'perplexity': {'score': 0.75, 'reasoning': 'test', 'raw_perplexity': 50},
            },
        }
        update_content_status('CTN-2024-06-15-TEST', classification_result)
        
        appeal_form = {
            'email': 'creator@example.com',
            'reasoning': 'This is a detailed explanation of why the classification is incorrect.',
            'writing_date': '2024-06-15',
            'process_duration_hours': 3,
            'writing_process': 'original composition',
            'native_language': 'English',
            'ai_assisted': False,
            'additional_context': 'Some context',
        }
        
        appeal_id = create_appeal(
            'CTN-2024-06-15-TEST',
            'creator@example.com',
            appeal_form,
            classification_result,
        )
        
        assert appeal_id != '', "Appeal ID should be generated"
        assert appeal_id.startswith('APP-'), "Appeal ID should start with APP-"
        print(f"✓ Appeal created with ID: {appeal_id}")
        
        appeal = get_appeal_detail(appeal_id)
        assert appeal is not None, "Appeal should be retrievable"
        assert appeal['content_id'] == 'CTN-2024-06-15-TEST', "Content ID should match"
        assert appeal['status'] == 'pending', "Appeal should be pending"
        print("✓ Appeal details correctly stored and retrieved")
        
    finally:
        cleanup_test_environment(test_dir, original_dir)


def test_reviewer_dashboard():
    """Test reviewer dashboard functionality."""
    print("\n[TEST 5] Reviewer Dashboard")
    
    test_dir, original_dir = setup_test_environment()
    
    try:
        classification_result = {
            'label': 'Your text is Likely AI-generated',
            'confidence': 0.75,
            'signals': {
                'llm_judgment': {'score': 0.8, 'reasoning': 'test'},
                'stylometry': {'score': 0.7, 'reasoning': 'test', 'subscores': {}},
                'perplexity': {'score': 0.75, 'reasoning': 'test', 'raw_perplexity': 50},
            },
        }
        update_content_status('CTN-2024-06-15-TEST', classification_result)
        
        appeal_form = {
            'email': 'creator@example.com',
            'reasoning': 'This is a detailed explanation of why the classification is incorrect.',
            'writing_date': '2024-06-15',
            'process_duration_hours': 3,
            'writing_process': 'original composition',
            'native_language': 'English',
            'ai_assisted': False,
        }
        
        appeal_id = create_appeal(
            'CTN-2024-06-15-TEST',
            'creator@example.com',
            appeal_form,
            classification_result,
        )
        
        pending = get_pending_appeals()
        assert len(pending) == 1, "Should have one pending appeal"
        assert pending[0]['appeal_id'] == appeal_id, "Appeal ID should match"
        print("✓ Pending appeals correctly listed")
        
        appeal = get_appeal_detail(appeal_id)
        formatted = format_appeal_for_reviewer(appeal)
        assert 'signal_breakdown' in formatted, "Signal breakdown should be present"
        assert 'original_classification' in formatted, "Classification should be present"
        print("✓ Appeal details correctly formatted for reviewer")
        
    finally:
        cleanup_test_environment(test_dir, original_dir)


def test_decision_submission():
    """Test reviewer decision submission."""
    print("\n[TEST 6] Reviewer Decision Submission")
    
    test_dir, original_dir = setup_test_environment()
    
    try:
        classification_result = {
            'label': 'Your text is Likely AI-generated',
            'confidence': 0.75,
            'signals': {
                'llm_judgment': {'score': 0.8, 'reasoning': 'test'},
                'stylometry': {'score': 0.7, 'reasoning': 'test', 'subscores': {}},
                'perplexity': {'score': 0.75, 'reasoning': 'test', 'raw_perplexity': 50},
            },
        }
        update_content_status('CTN-2024-06-15-TEST', classification_result)
        
        appeal_form = {
            'email': 'creator@example.com',
            'reasoning': 'This is a detailed explanation of why the classification is incorrect.',
            'writing_date': '2024-06-15',
            'process_duration_hours': 3,
            'writing_process': 'original composition',
            'native_language': 'English',
            'ai_assisted': False,
        }
        
        appeal_id = create_appeal(
            'CTN-2024-06-15-TEST',
            'creator@example.com',
            appeal_form,
            classification_result,
        )
        
        success, result = submit_decision(
            appeal_id,
            'reviewer@example.com',
            'approve',
            'After reviewing the creator appeal and original signals, I believe the classification was incorrect. The text shows clear human writing patterns.',
            'Recalibrate AI tool detection thresholds',
        )
        
        assert success == True, f"Decision should be submitted: {result}"
        assert result.startswith('DEC-'), "Decision ID should start with DEC-"
        print(f"✓ Approval decision submitted with ID: {result}")
        
        success, result = submit_decision(
            appeal_id,
            'reviewer@example.com',
            'deny',
            'The original classification stands. All signals align on AI-generation likelihood.',
        )
        
        assert success == False, "Should not allow decision on resolved appeal"
        print("✓ Correctly prevents multiple decisions on same appeal")
        
    finally:
        cleanup_test_environment(test_dir, original_dir)


def test_appeal_statistics():
    """Test appeal statistics generation."""
    print("\n[TEST 7] Appeal Statistics")
    
    test_dir, original_dir = setup_test_environment()
    
    try:
        classification_result = {
            'label': 'Your text is Likely AI-generated',
            'confidence': 0.75,
            'signals': {
                'llm_judgment': {'score': 0.8, 'reasoning': 'test'},
                'stylometry': {'score': 0.7, 'reasoning': 'test', 'subscores': {}},
                'perplexity': {'score': 0.75, 'reasoning': 'test', 'raw_perplexity': 50},
            },
        }
        
        for i in range(3):
            update_content_status(f'CTN-2024-06-15-T{i}', classification_result)
            appeal_form = {
                'email': f'creator{i}@example.com',
                'reasoning': 'This is a detailed explanation of why the classification is incorrect.',
                'writing_date': '2024-06-15',
                'process_duration_hours': 3,
                'writing_process': 'original composition',
                'native_language': 'English',
                'ai_assisted': False,
            }
            create_appeal(
                f'CTN-2024-06-15-T{i}',
                f'creator{i}@example.com',
                appeal_form,
                classification_result,
            )
        
        stats = get_appeal_statistics()
        assert stats['total_appeals'] == 3, "Should have 3 total appeals"
        assert stats['pending_appeals'] == 3, "All should be pending"
        print(f"✓ Statistics correctly generated: {stats}")
        
    finally:
        cleanup_test_environment(test_dir, original_dir)


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("APPEAL WORKFLOW INTEGRATION TESTS")
    print("=" * 60)
    
    tests = [
        test_appeal_form_validation,
        test_content_status_tracking,
        test_appeal_eligibility,
        test_appeal_creation,
        test_reviewer_dashboard,
        test_decision_submission,
        test_appeal_statistics,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
