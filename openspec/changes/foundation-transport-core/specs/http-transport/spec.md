## ADDED Requirements

### Requirement: Client construction and configuration

The library SHALL provide a synchronous `Client` and an asynchronous `AsyncClient`,
each constructible with an optional API `token`, a `base_url` (defaulting to the
VNDB production base URL, with a sandbox constant available), a request `timeout`,
a `user_agent`, and a retry configuration.

#### Scenario: Construct with defaults

- **WHEN** a `Client` (or `AsyncClient`) is created with no arguments
- **THEN** it targets the VNDB production base URL with default timeout, default
  user-agent, and default retry configuration, and sends no `Authorization` header

#### Scenario: Construct with a token

- **WHEN** a client is created with a `token`
- **THEN** every request it issues includes the header `Authorization: Token <token>`

#### Scenario: Inject a pre-built httpx client

- **WHEN** a client is created with a pre-built `httpx.Client` (or `AsyncClient`,
  e.g. one using `httpx.MockTransport`)
- **THEN** the client uses the injected instance for all requests instead of
  building its own

### Requirement: Client lifecycle

Each client SHALL support explicit closing and context-manager usage, and SHALL
close an httpx client it created itself while leaving an injected client open.

#### Scenario: Synchronous context manager

- **WHEN** a `Client` is used as `with Client() as c:`
- **THEN** on exit the underlying httpx client it created is closed

#### Scenario: Asynchronous context manager

- **WHEN** an `AsyncClient` is used as `async with AsyncClient() as c:`
- **THEN** on exit the underlying httpx client it created is closed via `aclose()`

#### Scenario: Injected client is not closed

- **WHEN** a client created with an injected httpx instance is closed
- **THEN** the injected httpx instance is left open for the caller to manage

### Requirement: Generic query primitive

Each client SHALL expose an internal generic query primitive that issues a POST
query to a given endpoint with the standard VNDB body parameters and returns a typed
`Page[T]` for a caller-supplied Pydantic model type.

#### Scenario: Query returns a typed page

- **WHEN** the generic query primitive is called for an endpoint with a model type
  and a successful response is returned
- **THEN** it returns a `Page[T]` whose `results` are instances of the given model
  type

#### Scenario: Standard body parameters are sent

- **WHEN** the generic query primitive is called with `filters`, `fields`, `sort`,
  `reverse`, `results`, `page`, and `count` values
- **THEN** the POST request body contains those parameters as defined by the VNDB API
