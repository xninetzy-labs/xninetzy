# architecture-analysis — §56

## 56. Example

Input:

src/domain/order.ts

Observed:

order.ts
 -> src/infrastructure/postgres/order-repository.ts

Metrics:

fan_in: 9
fan_out: 4
churn_90d: 21

Architecture inference:

order.ts
  layer = domain
  confidence = high

Declared rule:

domain
  cannot import
infrastructure

Finding:

ARCH-DIR-001
severity: HIGH
confidence: HIGH

Evidence:

src/domain/order.ts:12
direct import of infrastructure implementation

Potential refactor boundary:

Consumer:
  domain/order.ts

Concrete producer:
  infrastructure/postgres/order-repository.ts

Potential abstraction boundary:
  repository contract

No automatic refactor is performed.
