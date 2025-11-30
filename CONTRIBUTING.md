# Contributing to Vibe Agent

Thank you for considering contributing to Vibe Agent! This document provides guidelines and instructions for contributing.

## 🤝 Ways to Contribute

- **Bug Reports**: Report bugs via GitHub issues
- **Feature Requests**: Suggest new features or improvements
- **Code Contributions**: Submit pull requests
- **Documentation**: Improve docs and examples
- **Testing**: Add test coverage

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git
- Familiarity with FastAPI, Next.js, Neo4j

### Setup Development Environment

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/vibe-agent.git
cd vibe-agent

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Frontend setup
cd ../frontend
npm install

# Install pre-commit hooks
pre-commit install
```

## 📝 Development Workflow

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Changes

**Code Style:**
- **Python**: Follow PEP 8, use Black formatter
- **TypeScript**: Follow project ESLint config
- **Commits**: Use conventional commits (feat:, fix:, docs:, etc.)

**Testing:**
```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests (if applicable)
cd frontend  
npm test
```

### 3. Commit Changes
```bash
git add .
git commit -m "feat: add semantic search caching"
```

### 4. Push and Create PR
```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## 🧪 Testing Guidelines

### Backend Tests
```python
# tests/test_your_module.py
import pytest

class TestYourFeature:
    def test_something(self):
        # Arrange
        ...
        # Act
        ...
        # Assert
        assert expected == actual
```

**Test Coverage:**
- Aim for >80% coverage
- Test happy paths and edge cases
- Mock external dependencies (LLM, databases)

### Frontend Tests
- Component tests with React Testing Library
- Integration tests for API calls
- E2E tests with Playwright (optional)

## 📋 Pull Request Guidelines

**PR Checklist:**
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] PR description explains changes

**PR Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
How was this tested?

## Screenshots (if applicable)
```

## 🎯 Priority Areas

**High Priority:**
- Performance optimizations
- Additional language support (Java, Go, Rust)
- UI/UX improvements
- Test coverage expansion

**Medium Priority:**
- Advanced graph visualizations
- Incremental indexing
- Multi-repository support

**Low Priority:**
- Alternative LLM backends
- Cloud deployment guides
- Browser extension

## 📚 Code Organization

```
backend/
  src/
    indexing/      # File discovery, AST parsing
    intelligence/  # Code analysis, health
    graphs/        # Neo4j integration
    embeddings/    # BGE-M3, FAISS
    retrieval/     # Search, ranking
    memory/        # Error tracking
    agents/        # AI agents
    reasoning/     # LLM integration
    patching/      # Diff generation
    app/          # FastAPI routes

frontend/
  src/
    app/          # Next.js pages
    components/   # React components
    lib/          # API client
    store/        # State management
    styles/       # CSS
```

## 🐛 Bug Reports

**Good Bug Report Includes:**
1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Minimal steps to reproduce
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: OS, Python/Node versions
6. **Logs**: Relevant error messages

## 💡 Feature Requests

**Good Feature Request Includes:**
1. **Use Case**: Why is this feature needed?
2. **Proposed Solution**: How should it work?
3. **Alternatives**: Other approaches considered
4. **Additional Context**: Examples, mockups

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- GitHub contributors page

## 📧 Questions?

- GitHub Issues: For bugs and features
- GitHub Discussions: For general questions
- Email: [your-email] for private concerns

---

**Thank you for contributing to Vibe Agent!** 🎉
