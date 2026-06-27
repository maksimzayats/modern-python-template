# diwire Reference

Use this file when creating or updating dependency injection with `diwire`,
`Injected[...]`, container setup, explicit bindings, entrypoint resolution, or
test overrides.

## Contents

- [Class Injection](#class-injection)
- [Container Setup](#container-setup)
- [Explicit Bindings](#explicit-bindings)
- [Entrypoints](#entrypoints)
- [Test Overrides](#test-overrides)
- [Anti-Patterns](#anti-patterns)

## Class Injection

Injectable classes should usually be keyword-only dataclasses. Inject
dependencies as private fields typed with `Injected[DependencyType]`.

```python
from dataclasses import dataclass

from diwire import Injected


@dataclass(frozen=True, kw_only=True)
class RegisterUserCommand:
    email: str
    password: str


@dataclass(kw_only=True)
class PasswordHasher:
    def hash_password(self, *, raw_password: str) -> str:
        return f"hashed:{raw_password}"


@dataclass(kw_only=True)
class UserStore:
    def create_user(self, *, email: str, password_hash: str) -> int:
        # Replace with the repo's persistence style.
        return 1


@dataclass(kw_only=True)
class RegisterUserUseCase:
    _password_hasher: Injected[PasswordHasher]
    _user_store: Injected[UserStore]

    def execute(self, *, command: RegisterUserCommand) -> int:
        password_hash = self._password_hasher.hash_password(
            raw_password=command.password,
        )
        return self._user_store.create_user(
            email=command.email,
            password_hash=password_hash,
        )
```

Prefer concrete dependency types for project-owned, framework-free
collaborators. Use a narrow adapter or justified ABC when the dependency is
external IO, framework-bound, selected by configuration, or has multiple real
implementations.

## Container Setup

Use `diwire` auto-wiring so most concrete classes need no manual registration.
For new repos, prefer explicit recursive policies so the intended wiring
behavior is visible:

```python
from diwire import Container, DependencyRegistrationPolicy, MissingPolicy


def get_container() -> Container:
    container = Container(
        missing_policy=MissingPolicy.REGISTER_RECURSIVE,
        dependency_registration_policy=DependencyRegistrationPolicy.REGISTER_RECURSIVE,
    )

    register_dependencies(container)
    return container


def register_dependencies(container: Container) -> None:
    # Keep this empty until explicit binding is genuinely needed.
    pass
```

If an existing repo uses plain `Container()` or another valid `diwire`
configuration, preserve its local container style.

## Explicit Bindings

Add explicit registration only for abstractions, factory classes, existing
instances, or external adapter bindings:

```python
from diwire import Container


def register_dependencies(container: Container) -> None:
    container.add(SmtpEmailSender, provides=EmailSender)
```

Keep explicit registration in `ioc/`. Do not register bindings from use cases,
services, or delivery adapters.

## Entrypoints

Entrypoints resolve the outer application object or use case at the edge:

```python
def main() -> None:
    container = get_container()
    use_case = container.resolve(RegisterUserUseCase)

    user_id = use_case.execute(
        command=RegisterUserCommand(
            email="ada@example.com",
            password="correct horse battery staple",
        ),
    )
    print(user_id)
```

Framework entrypoints should create or receive the application container at the
outer edge, then resolve use cases there. Do not pass the container deeper into
application code.

## Test Overrides

Tests override dependencies before resolving the target graph:

```python
from dataclasses import dataclass


@dataclass(kw_only=True)
class FakePasswordHasher(PasswordHasher):
    def hash_password(self, *, raw_password: str) -> str:
        return f"fake:{raw_password}"


def test_register_user() -> None:
    container = get_container()
    container.add_instance(FakePasswordHasher(), provides=PasswordHasher)

    use_case = container.resolve(RegisterUserUseCase)

    user_id = use_case.execute(
        command=RegisterUserCommand(email="ada@example.com", password="secret"),
    )

    assert user_id == 1
```

Prefer real deterministic services in tests. Override IO, time, randomness,
external adapters, and framework resources before resolving the target object.

## Anti-Patterns

- Do not inject `Container`.
- Do not call `container.resolve()` inside use cases or services.
- Do not use global singletons as a substitute for explicit composition.
- Do not add explicit registrations for every concrete class when auto-wiring is
  sufficient.
- Do not instantiate collaborators inside use cases/services unless they are
  simple values.
