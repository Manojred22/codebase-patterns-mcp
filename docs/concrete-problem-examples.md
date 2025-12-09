# Concrete Problem Examples: Example API Project Development

**Context:** A developer built this 3-API microservice with Claude while being new to the codebase. Multiple iterations required because Claude lacked codebase-specific context.

---

## Git History Analysis

### Summary Statistics
- **Total commits:** 50+ commits
- **Review-related iterations:** 6+ commits
- **Dead code removed:** ~1,800 lines
- **Major refactors:** 4+ (naming conventions, schema restructure, template reuse)
- **Time wasted:** Estimated 8-12 hours on rework

---

## Problem 1: Wrong Naming Conventions

### What Happened
Claude generated code using generic naming:
```
internal/storage/gorm/
├── models/
├── repository/
└── mocks/
```

**Problem:** The codebase doesn't use "gorm" in path names, uses "mysql" (the database, not the library)

**Required change:** Rename all files/directories from `gorm` → `mysql`
```
internal/storage/mysql/   # ✅ Codebase convention
```

**Files changed:** 7 files, 483 insertions

### How MCP Would Have Helped

**Claude asks:** "Create repository layer with GORM"

**MCP search:** `repository pattern database`

**MCP returns:** Existing repos using structure:
```go
// From similar service
internal/storage/mysql/repository/user.go
internal/storage/mysql/models/user.go
```

**Claude would have used:** Correct `mysql` naming from the start

---

## Problem 2: Reinventing CI/CD Workflows

### What Happened
Claude created new GitHub Actions workflows from scratch instead of reusing existing templates.

**Files changed:**
- `.github/workflows/deploy-development.yml` - Rewrote to use templates
- `.github/workflows/deploy-staging.yml` - Rewrote to use templates
- `.github/workflows/migrate-db.yml` - Added (55 new lines)
- `docs.mk` - Deleted (58 lines) - was doing this manually

**Before (Claude generated):**
```yaml
# Custom workflow, duplicated logic
name: Deploy Development
on: push
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - checkout
      - setup go
      - build
      - deploy
      # ... 50+ lines of custom logic
```

**After (using existing templates):**
```yaml
name: Deploy Development
on: push
jobs:
  deploy:
    uses: ./.github/workflows/reusable-deploy.yml  # ✅ Reusable template
    with:
      environment: development
```

### How MCP Would Have Helped

**Claude asks:** "Create CI/CD pipeline for Go service"

**MCP search:** `github actions deploy workflow`

**MCP returns:**
- Template workflows from other services
- Reusable workflow patterns
- Migration workflow examples

**Claude would have:** Used existing templates, not reinvented them

---

## Problem 3: REST API Schema Not Following Project Guidelines

### What Happened
Claude generated OpenAPI schemas that didn't follow the project's REST API Guidelines.

**Files changed:** 4 schema files, 92 insertions, 124 deletions (net -32 lines = simpler!)

**Guideline (from RestGuidelines.md):**
> "Resource URIs should be based on nouns representing the resources"
> "Design APIs around core business entities"

**Before (Claude generated):**
```json
{
  "paths": {
    "/create-account": {  // ❌ Verb in URI
      "post": { ... }
    },
    "/get-account/{id}": {  // ❌ Verb in URI
      "get": { ... }
    }
  }
}
```

**After (following guidelines):**
```json
{
  "paths": {
    "/accounts": {  // ✅ Noun, collection
      "post": { ... }
    },
    "/accounts/{id}": {  // ✅ Noun, resource
      "get": { ... }
    }
  }
}
```

**Also fixed:** Error response format, pagination structure, metadata fields

### How MCP Would Have Helped

**Claude asks:** "Create REST API for sandbox account management"

**MCP search:** `REST API handler account endpoint`

**MCP returns:**
- Existing API handlers following guidelines
- OpenAPI schemas from other services
- Error response formats
- Pagination examples

**Plus:** MCP could return guideline excerpts themselves if indexed

**Claude would have:** Followed resource-based URIs, correct error formats from the start

---

## Problem 4: Generated 1,843 Lines of Dead Code

### What Happened
Claude over-engineered and generated unnecessary abstractions.

**Files deleted:**
- Old integration tests: 670 lines
- Duplicate test helpers: 144 lines
- Unused test builders: 202 lines
- Old repository implementations: 481 lines
- Duplicate mocks: 193 lines
- Unused models: 30 lines

**Total waste:** 1,843 lines written, reviewed, then deleted

**Example dead code:**
```go
// Claude generated this complex test data builder...
type AccountBuilder struct {
    account *models.Account
    // ... 15 fields
}

func (b *AccountBuilder) WithEmail(email string) *AccountBuilder { ... }
func (b *AccountBuilder) WithCountry(country string) *AccountBuilder { ... }
// ... 10 more builder methods

// But org uses simple fixtures:
func NewTestAccount() *models.Account {
    return &models.Account{Email: "test@test.com", Country: "AE"}
}
```

### How MCP Would Have Helped

**Claude asks:** "Create test helpers for account models"

**MCP search:** `test helpers fixtures account`

**MCP returns:** Simple fixture patterns from other services

**Claude would have:** Generated minimal test helpers, not over-engineered builders

---

## Problem 5: Multiple Review Iteration Cycles

### What Happened

**6 separate commits** for review feedback:
- `cb2321c - Review changes 2` (19 files, -713 lines net)
- `323a4b0 - Review changes` (22 files, 263/213 changes)
- `a87d092 - review changes final`
- `671a8aa - review changes`
- `0174507 - changes for Review comments 2`
- `9a330ab - Review comments`

**Common issues found in reviews:**
1. Service layer too complex (simplified in review)
2. Unnecessary validation logic (removed)
3. Wrong error handling patterns (fixed)
4. Test structure not matching org standards
5. Swagger documentation incomplete

**Example from commit `323a4b0`:**

```diff
// Before (Claude generated)
func (s *AccountServiceImpl) CreateAccount(ctx context.Context, req CreateAccountRequest) (*AccountResponse, error) {
    // 45 lines of inline logic
    if err := s.validateRequest(req); err != nil {
        return nil, err
    }
    if err := s.checkDuplicates(req); err != nil {
        return nil, err
    }
    // ... lots more inline validation
}

// After (review feedback)
func (s *AccountServiceImpl) CreateAccount(ctx context.Context, req CreateAccountRequest) (*AccountResponse, error) {
    // 12 lines - simpler, reuses existing patterns
    account, err := s.buildAccount(req)  // ✅ Reuses helper
    if err != nil {
        return nil, err
    }
    // ...
}
```

### How MCP Would Have Helped

**Claude asks:** "Create account service with business logic"

**MCP search:** `service layer business logic CRUD`

**MCP returns:**
- Service patterns from other business modules
- Error handling conventions
- Validation patterns
- Logging/tracing patterns

**Result:** First draft would match org patterns, fewer review cycles

---

## Problem 6: Wrong Test Patterns

### What Happened
**Commits:** `827eae4 - table driven test`, `6cce42d - table driven test`

Claude initially generated standard Go tests, but org uses table-driven tests.

**Before (Claude):**
```go
func TestCreateAccount_Success(t *testing.T) { ... }
func TestCreateAccount_InvalidEmail(t *testing.T) { ... }
func TestCreateAccount_DuplicateAccount(t *testing.T) { ... }
// 8 separate test functions
```

**After (org pattern):**
```go
func TestCreateAccount(t *testing.T) {
    tests := []struct{
        name string
        input CreateAccountRequest
        want *Account
        wantErr bool
    }{
        {name: "success", ...},
        {name: "invalid email", ...},
        {name: "duplicate", ...},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) { ... })
    }
}
```

### How MCP Would Have Helped

**Claude asks:** "Write unit tests for account service"

**MCP search:** `unit test service table driven`

**MCP returns:** Table-driven test examples from codebase

**Claude would have:** Used table-driven pattern from the start

---

## Problem 7: Didn't Know About Existing HTTP Client Patterns

### What Happened

Claude generated new HTTP client for B2B Orchestrator from scratch, but org has standard patterns.

**What Claude generated:**
```go
// Reinvented HTTP client with custom retry, timeout, error handling
type B2BClient struct {
    baseURL string
    timeout time.Duration
    retries int
}

func (c *B2BClient) Post(endpoint string, body interface{}) (*Response, error) {
    // 50+ lines of custom HTTP logic
}
```

**What org already had (from other services):**
```go
// Standard client from go-sre library
import "github.com/Propertyfinder/go-sre/httpclient"

client := httpclient.New(
    httpclient.WithRetry(3),
    httpclient.WithTimeout(30*time.Second),
)
```

**Had to refactor** after realizing the pattern existed

### How MCP Would Have Helped

**Claude asks:** "Create HTTP client for external API"

**MCP search:** `HTTP client external API retry`

**MCP returns:**
- Existing `pkg/httpclient` package
- Usage examples from other services
- Configuration patterns

**Claude would have:** Used existing client library, not reinvented it

---

## Summary: What Claude Didn't Know

| Category | What Claude Lacked | Impact |
|----------|-------------------|--------|
| **Naming conventions** | `mysql` vs `gorm` in paths | 483 lines renamed |
| **Reusable templates** | GitHub Actions workflows | 58 deleted, rewrote 3 files |
| **REST guidelines** | Resource URIs, error formats | 4 files restructured |
| **Code patterns** | Service/repo/handler patterns | 6 review cycles |
| **Test patterns** | Table-driven tests | Rewrote tests |
| **Existing libraries** | go-sre HTTP client, others | Reinvented wheels |
| **Org architecture** | Layer separation, error handling | 1,843 dead lines |

---

## How MCP Would Have Prevented This

### Scenario 1: Starting the Project

**Without MCP (what happened):**
```
You: "Create a Go microservice for sandbox provisioning with 3 APIs"
Claude: *generates generic Go code*
You: *spends 12 hours over 6 review cycles fixing*
```

**With MCP:**
```
You: "Create a Go microservice for sandbox provisioning with 3 APIs"
Claude: *calls search_code("microservice structure Go API")*
MCP: *returns: enterprise-api-example structure, similar services*
Claude: "I found your org's microservice structure. I'll follow this pattern:
        - internal/apps/ for handlers
        - internal/business/ for services
        - internal/storage/mysql/ for repos
        - Use go-sre libraries
        Should I proceed?"
You: "Yes"
Claude: *generates code matching YOUR patterns*
```

### Scenario 2: Creating API Endpoints

**Without MCP:**
```
You: "Add POST /create-account endpoint"
Claude: *generates /create-account with verb*
Reviewer: "Use RESTful URIs - POST /accounts"
You: *refactors*
```

**With MCP:**
```
You: "Add endpoint to create accounts"
Claude: *calls search_code("REST API endpoint create resource")*
MCP: *returns: existing handlers, REST guidelines*
Claude: "I found your REST conventions. I'll create POST /accounts
        following your guideline of noun-based URIs."
```

### Scenario 3: Writing Tests

**Without MCP:**
```
You: "Write tests for CreateAccount"
Claude: *generates 8 separate test functions*
Reviewer: "Use table-driven tests"
You: *refactors to table-driven*
```

**With MCP:**
```
You: "Write tests for CreateAccount"
Claude: *calls search_code("unit test service")*
MCP: *returns: table-driven test examples*
Claude: *generates table-driven tests from the start*
```

---

## Time & Cost Savings Estimate

**Actual development (without MCP):**
- Initial development: ~20 hours
- Review cycles: ~8 hours
- Rework: ~4 hours
- **Total: ~32 hours**

**Estimated with MCP:**
- Initial development: ~18 hours (slightly slower due to MCP queries)
- Review cycles: ~2 hours (mostly business logic review)
- Rework: ~1 hour (minor fixes)
- **Total: ~21 hours**

**Savings: 11 hours (34% faster)**

**Scaled to team:**
- 10 developers × 11 hours saved per project = 110 hours
- 5 projects per year = **550 hours saved annually**
- At $100/hour = **$55,000 saved**

---

## Key Insight

The problem isn't that Claude is bad at code generation.

**The problem is:** Claude doesn't know **YOUR** org's:
- Naming conventions
- Existing libraries
- REST guidelines
- Test patterns
- Project structure
- CI/CD templates

**MCP solves this** by giving Claude searchable access to your existing code.

Claude becomes **codebase-aware**, not just code-aware.
