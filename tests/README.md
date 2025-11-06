# IntelliAudit Test Suite

## Quick Start

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_auditor_agent.py

# Run with verbose output
pytest -v -s
```

## Test Structure

```
tests/
  unit/              # Unit tests for individual components
    test_auditor_agent.py
    test_search_agent.py
    test_judge_agent.py
    test_defender_agent.py
  
  integration/       # Integration tests for agent interactions
    test_agent_interactions.py
    test_langgraph_workflows.py
  
  fixtures/          # Test data fixtures
    evidence/
    controls/
  
  helpers/           # Test helper utilities
```

## Current Test Coverage

### ✅ Implemented
- Policy Control (5.1) evaluator tests
- Access Control (5.15) evaluator tests  
- Asset Control (5.9) evaluator tests
- Business Continuity (5.29) evaluator tests
- Control category mapping tests
- Status determination logic tests
- Search agent control lookup tests
- Basic integration tests

### 🚧 TODO
- Data Classification (5.12) evaluator tests
- Compliance Review (5.31-5.37) evaluator tests
- Risk Assessment evaluator tests
- Monitoring Logs evaluator tests
- Training Records evaluator tests
- LangGraph workflow state inspection tests
- Error handling edge cases
- Performance tests

## Running Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Tests marked with specific marker
pytest -m unit
pytest -m integration
```

## Coverage Goals

- **Current**: ~30% (basic tests)
- **Target**: 80%+ for evaluator functions
- **Focus**: 5 core controls (5.1, 5.12, 5.15, 5.9, 5.29-5.30)

