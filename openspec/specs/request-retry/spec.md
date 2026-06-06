# request-retry Specification

## Purpose
TBD - created by archiving change foundation-transport-core. Update Purpose after archive.
## Requirements
### Requirement: Configurable bounded retry

The library SHALL provide a `RetryConfig` controlling the maximum number of attempts
and the backoff schedule, and SHALL bound all retrying by the configured maximum,
raising the final error once attempts are exhausted.

#### Scenario: Retry then succeed

- **WHEN** a request receives a retryable response (e.g. HTTP 429) and then a
  successful response on retry, within the attempt limit
- **THEN** the client returns the successful result

#### Scenario: Attempts exhausted

- **WHEN** a request keeps receiving a retryable error beyond the configured maximum
  attempts
- **THEN** the client raises the mapped error for the last response

### Requirement: Retry classification

The retry decision SHALL be a pure function of the attempt number, the response
status (if any), and the raised exception (if any). It SHALL retry on HTTP 429,
transient server errors (502, 503), and httpx network/timeout errors, and SHALL NOT
retry on 400, 401, 404, or Pydantic validation errors.

#### Scenario: Non-retryable client error

- **WHEN** a request receives HTTP 400, 401, or 404
- **THEN** no retry occurs and the corresponding error is raised immediately

#### Scenario: Retryable network error

- **WHEN** a request raises an httpx connect/read/timeout error within the attempt
  limit
- **THEN** the request is retried

#### Scenario: Pure decision without I/O

- **WHEN** the retry policy is evaluated with synthetic `(attempt, status, exception)`
  inputs
- **THEN** it returns whether to retry and the delay without performing any network
  call or real sleep

### Requirement: Backoff timing

On any retryable response the client SHALL honor a `Retry-After` response header
when present (not only on 429); otherwise it SHALL apply exponential backoff with
a cap. The sleep mechanism SHALL be patchable so tests do not wait in real time.

#### Scenario: Honor Retry-After

- **WHEN** a retryable response (e.g. 429 or a transient 502/503) includes a
  `Retry-After` header and a retry will occur
- **THEN** the client waits for the indicated duration before retrying

#### Scenario: Exponential backoff without Retry-After

- **WHEN** a retryable response has no `Retry-After` header
- **THEN** the client waits for an exponentially increasing, capped delay before
  retrying

