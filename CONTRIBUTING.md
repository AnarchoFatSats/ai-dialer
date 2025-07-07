# Contributing to AI Voice Dialer

We love your input! We want to make contributing to the AI Voice Dialer as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to sync code, track issues and feature requests, as well as accept pull requests.

### Pull Requests Process

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Development Setup

### 1. Fork & Clone
```bash
# Fork the repository on GitHub, then:
git clone https://github.com/yourusername/ai-voice-dialer.git
cd ai-voice-dialer

# Add upstream remote
git remote add upstream https://github.com/original-owner/ai-voice-dialer.git
```

### 2. Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Copy environment file
cp env.example .env
# Edit .env with your test API keys
```

### 3. Database Setup
```bash
# Start test database
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Create test data
python scripts/create_test_data.py
```

### 4. Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run AI system tests
python test_ai_system.py
```

## Code Style

We use these tools to maintain code quality:

### Formatting
```bash
# Auto-format Python code
black app/
black tests/

# Sort imports
isort app/ tests/
```

### Linting
```bash
# Python linting
flake8 app/
pylint app/

# Type checking
mypy app/
```

### Pre-commit Hooks
We recommend setting up pre-commit hooks:

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

## Testing Guidelines

### Unit Tests
- Write tests for all new functions and classes
- Place tests in `tests/` directory with matching structure
- Use descriptive test names: `test_ai_conversation_handles_transfer_request()`
- Mock external services (Twilio, AI APIs) in tests

### Integration Tests
- Test complete workflows end-to-end
- Use test database and Redis instances
- Test API endpoints with realistic data

### AI Service Tests
- Mock AI service responses for speed
- Include real API tests in separate suite
- Test error handling and timeouts

### Example Test Structure
```python
# tests/services/test_ai_conversation.py
import pytest
from unittest.mock import AsyncMock, patch
from app.services.ai_conversation import ai_conversation_engine

class TestAIConversationEngine:
    @pytest.mark.asyncio
    async def test_start_conversation_creates_context(self):
        """Test that starting a conversation creates proper context."""
        # Test implementation
        
    @pytest.mark.asyncio
    @patch('app.services.ai_conversation.anthropic.AsyncAnthropic')
    async def test_generate_ai_response_with_mock(self, mock_anthropic):
        """Test AI response generation with mocked service."""
        # Test implementation with mocked Claude API
```

## Documentation

### Code Documentation
- Use docstrings for all public functions and classes
- Follow Google-style docstrings
- Include parameter types and return types
- Add usage examples for complex functions

```python
async def initiate_call(self, lead_id: int, campaign_id: int, did_id: int) -> Dict[str, Any]:
    """Initiate an outbound call with AI conversation flow.
    
    Args:
        lead_id: ID of the lead to call
        campaign_id: ID of the campaign
        did_id: ID of the DID to use for calling
        
    Returns:
        Dict containing call status and metadata
        
    Raises:
        ValueError: If lead, campaign, or DID not found
        TwilioRestException: If Twilio API call fails
        
    Example:
        result = await twilio_service.initiate_call(123, 456, 789)
        print(f"Call initiated: {result['call_sid']}")
    """
```

### API Documentation
- Update OpenAPI descriptions in FastAPI decorators
- Add request/response examples
- Document error codes and messages

### README Updates
- Update feature lists when adding new capabilities
- Add new API endpoints to the examples
- Update deployment instructions if needed

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, missing semi colons, etc)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvements
- `test`: Adding missing tests or correcting existing tests
- `build`: Changes that affect the build system or external dependencies
- `ci`: Changes to CI configuration files and scripts

### Examples
```bash
feat(ai): add Claude 3.5 Sonnet support for better conversations
fix(twilio): handle webhook timeouts gracefully
docs(api): update campaign creation examples
test(did): add DID rotation integration tests
refactor(cost): optimize budget calculation performance
```

## Feature Development

### 1. Planning
- Open an issue to discuss the feature before coding
- Get feedback from maintainers and community
- Break down large features into smaller, manageable PRs

### 2. Implementation
- Create feature branch: `feature/your-feature-name`
- Implement with tests and documentation
- Keep commits focused and atomic
- Follow existing code patterns and architecture

### 3. AI Services Integration
When adding new AI services:
- Add configuration in `app/config.py`
- Create service wrapper in `app/services/`
- Add proper error handling and retries
- Include usage cost tracking
- Add health checks and monitoring

### 4. Database Changes
- Create Alembic migrations for schema changes
- Test migrations in both directions (up/down)
- Consider data migration needs
- Update model documentation

## Bug Reports

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/yourusername/ai-voice-dialer/issues/new).

### Great Bug Reports Include:
- A quick summary and/or background
- Steps to reproduce (be specific!)
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

### Bug Report Template
```markdown
**Bug Description**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
A clear and concise description of what you expected to happen.

**Screenshots/Logs**
If applicable, add screenshots or log outputs to help explain your problem.

**Environment**
- OS: [e.g. macOS, Ubuntu 20.04]
- Python version: [e.g. 3.12.0]
- Docker version: [e.g. 20.10.21]
- API versions: [Twilio, Claude, etc.]

**Additional Context**
Add any other context about the problem here.
```

## Feature Requests

We welcome feature requests! Please:

1. Check if the feature already exists or is planned
2. Open a GitHub issue with the "enhancement" label
3. Describe the use case and why it would be valuable
4. Include mockups or examples if applicable

### Feature Request Template
```markdown
**Is your feature request related to a problem?**
A clear and concise description of what the problem is.

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions you've considered.

**Use Case**
Describe how this feature would be used and who would benefit.

**Additional Context**
Add any other context or screenshots about the feature request here.
```

## Performance Guidelines

### Code Performance
- Use async/await for I/O operations
- Implement proper caching where appropriate
- Monitor database query performance
- Profile AI service response times

### AI Service Optimization
- Implement request batching where possible
- Use appropriate model sizes for the task
- Cache frequently used AI responses
- Monitor token usage and costs

### Database Optimization
- Use appropriate indexes
- Implement connection pooling
- Monitor slow queries
- Use read replicas for analytics

## Security Guidelines

### API Security
- Never commit API keys or secrets
- Use environment variables for configuration
- Implement proper input validation
- Add rate limiting to public endpoints

### Data Protection
- Encrypt sensitive data at rest
- Use HTTPS for all communications
- Implement proper access controls
- Follow GDPR/CCPA guidelines for data handling

### Webhook Security
- Validate webhook signatures
- Use HTTPS endpoints only
- Implement replay attack protection
- Log security events

## Review Process

### Code Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass and provide good coverage
- [ ] Documentation is updated
- [ ] No secrets or API keys committed
- [ ] Performance implications considered
- [ ] Security implications reviewed
- [ ] AI service costs considered
- [ ] Backwards compatibility maintained

### Review Criteria
- **Functionality**: Does the code do what it's supposed to do?
- **Performance**: Are there any performance implications?
- **Security**: Are there any security vulnerabilities?
- **Maintainability**: Is the code readable and maintainable?
- **Tests**: Is there adequate test coverage?
- **Documentation**: Is the code properly documented?

## Community

### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and community discussion
- **Discord**: Real-time chat and collaboration
- **Email**: security@yourcompany.com for security issues

### Code of Conduct
We are committed to providing a welcoming and inclusive experience for everyone. We expect all community members to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

### Getting Help
- Check existing issues and documentation first
- Ask questions in GitHub Discussions
- Join our Discord for real-time help
- Tag maintainers in issues when appropriate

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

## Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes for significant contributions
- Hall of Fame for major contributions

Thank you for contributing to AI Voice Dialer! 🚀 