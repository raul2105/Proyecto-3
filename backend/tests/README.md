# Test Suite for Flexo Inspection System

## Structure

```
tests/
├── unit/               # Unit tests for individual modules
├── integration/        # Integration tests for module interactions
├── fixtures/           # Test fixtures and mock data
└── datasets/           # Test datasets for replay simulator
```

## Running Tests

### All Tests
```bash
cd backend
pytest
```

### Unit Tests Only
```bash
pytest tests/unit -v
```

### Integration Tests Only
```bash
pytest tests/integration -v
```

### With Coverage
```bash
pytest --cov=. --cov-report=html --cov-report=term
```

### Specific Test File
```bash
pytest tests/unit/test_schemas.py -v
```

### Specific Test Function
```bash
pytest tests/unit/test_schemas.py::test_defect_event_creation -v
```

## Test Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow tests (skip with `-m "not slow"`)

## Writing Tests

### Unit Test Template
```python
import pytest

def test_function_name():
    """Test description"""
    # Arrange
    input_data = ...
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_value
```

### Integration Test Template
```python
import pytest

@pytest.mark.integration
def test_integration_scenario():
    """Test multi-module integration"""
    # Setup
    module_a = ModuleA()
    module_b = ModuleB()
    
    # Execute workflow
    result = module_a.process()
    final_result = module_b.consume(result)
    
    # Verify
    assert final_result.is_valid()
```

## Continuous Integration

Tests are automatically run on every push and pull request via GitHub Actions.
See `.github/workflows/ci.yml` for details.

## Coverage Goals

- Overall coverage target: >80%
- Critical modules (sync, inspection, decision): >90%
- New code: 100% coverage required
