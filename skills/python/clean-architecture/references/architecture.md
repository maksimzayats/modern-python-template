# Architecture Reference

Use this file when creating or refactoring package structure, application
boundaries, use cases, services, DTOs, schemas, persistence boundaries, or
abstractions.

## Contents

- [Target Shape](#target-shape)
- [Feature Slice](#feature-slice)
- [Dependency Rules](#dependency-rules)
- [Use Cases vs Services](#use-cases-vs-services)
- [DTOs and Schemas](#dtos-and-schemas)
- [Abstractions](#abstractions)
- [Completion Checklist](#completion-checklist)

## Target Shape

Prefer this package structure for non-trivial apps:

```text
src/<package_name>/
  core/
  foundation/
  infrastructure/
  entrypoints/
  ioc/
```

Use the folders when they clarify real boundaries:

| Folder | Purpose |
| --- | --- |
| `core/` | Application behavior, domain models, DTOs, use cases, and focused services. |
| `foundation/` | Tiny stable primitives, marker bases, common exceptions, or justified ABCs. |
| `infrastructure/` | External libraries, framework integration, persistence, clients, and adapters. |
| `entrypoints/` | Application bootstrapping, top-level app objects, CLI mains, worker startup, or other composition edges. |
| `ioc/` | `diwire.Container` creation and explicit dependency registration. |

For small repos, do not create empty folders just to match the shape. Introduce
structure as the boundary becomes useful.

Do not put business workflows, framework code, or infrastructure imports in
`foundation/`.

## Feature Slice

One small feature slice may look like this:

```text
src/<package_name>/
  core/users/register_user.py
  core/users/password_hasher.py
  core/notifications/email_sender.py
  core/users/delivery/<framework>/controller.py
  infrastructure/notifications/smtp_email_sender.py
  entrypoints/cli.py
  ioc/container.py
```

Delivery adapters may live in a domain-owned delivery folder such as
`core/<domain>/delivery/<framework>/`, or in an outer adapter package, depending
on the repo's existing convention. Even when delivery lives under `core/`, use
cases and services must not import delivery concerns.

## Dependency Rules

Use these rules unless the repo already has a stronger local convention:

- Delivery adapters call use cases or application services. Direct calls to
  focused services are acceptable only for very small workflows.
- Use cases coordinate externally meaningful application actions.
- Services encapsulate focused reusable behavior.
- Infrastructure code may depend on external libraries and framework APIs.
- Composition code in `entrypoints/` and `ioc/` may import across layers to wire
  objects together, but it should not contain application logic.
- Tests may cross runtime boundaries when testing integration behavior or
  architecture guardrails.

Do not create generic `Manager`, `Helper`, `Utils`, or vague `Handler` classes.
Name the class after the action or behavior it owns.

## Use Cases vs Services

Choose one class when one class is enough.

Use a use case for an externally meaningful application action, especially
something an entrypoint calls directly:

- `CreateUserUseCase`
- `IssueTokenUseCase`
- `ImportOrdersUseCase`

Use a service for focused behavior reused by one or more use cases:

- `PasswordHasher`
- `TokenIssuer`
- `OrderPricingService`
- `InventoryReservationService`

Split responsibilities because behavior differs, not because there are many
domain nouns.

## DTOs and Schemas

- Use small command DTOs when a use-case method would otherwise take several
  related fields.
- Return explicit result DTOs when returning multiple values or crossing a
  delivery boundary.
- Keep request/response schemas in the delivery adapter layer when the repo has
  one.
- Keep mapping boring and local. Add mapper classes only when mapping is complex
  or duplicated.
- Do not pass framework request/response objects or delivery schemas into use
  cases/services.

If the repo uses an ORM, do not hide that fact with unnecessary abstractions.
Keep ORM access out of delivery code and place it behind use cases, services, or
justified persistence adapters. Move persistence-heavy or framework-bound
queries into focused persistence services/adapters once they grow beyond simple
project-owned behavior.

## Abstractions

Do not introduce an ABC, interface, or protocol just because dependency
injection is present.

Default to concrete classes when there is one implementation and no meaningful
boundary pressure. Use an ABC only when it protects a real boundary, such as:

- multiple implementations selected by configuration;
- an external system or framework adapter hidden behind an application contract;
- a dependency that must be replaced cleanly in tests and cannot be represented
  by a concrete project type.

For this style, prefer `ABC` over `Protocol` for local explicit contracts when
an abstraction is genuinely needed. Leave existing useful `Protocol`s alone, and
use a `Protocol` only when structural typing is clearly the better fit. Do not
add new local `Protocol` types by default.

```python
# src/<package_name>/core/notifications/email_sender.py
from abc import ABC, abstractmethod


class EmailSender(ABC):
    @abstractmethod
    def send_welcome_email(self, *, email: str) -> None: ...
```

```python
# src/<package_name>/infrastructure/notifications/smtp_email_sender.py
from dataclasses import dataclass

# Replace `example` with the repo's package name.
from example.core.notifications.email_sender import EmailSender


@dataclass(kw_only=True)
class SmtpEmailSender(EmailSender):
    def send_welcome_email(self, *, email: str) -> None:
        # External SMTP integration belongs in infrastructure.
        raise NotImplementedError
```

Bind the concrete adapter in `ioc/`, not inside the use case.

## Completion Checklist

Check:

- Use cases/services do not import delivery adapters, framework entrypoint
  objects, request/response schemas, or `diwire.Container`.
- External IO and framework-bound dependencies are at the edge or behind a
  justified adapter.
- `foundation/` contains only stable cross-layer primitives.
- Explicit container registrations are limited to abstractions, factories,
  existing instances, or external adapter bindings.
- No abstractions were added only for ceremony.
