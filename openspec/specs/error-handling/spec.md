# error-handling Specification

## Purpose
TBD - created by archiving change foundation-transport-core. Update Purpose after archive.
## Requirements
### Requirement: Exception hierarchy

The library SHALL define a base `VndbError` and an API-error type carrying the HTTP
status code and the response body message, with distinct subclasses for bad request
(400), authentication (401), not found (404), rate limit (429), and server errors
(5xx), plus a network-error type for transport/timeout failures. All raised errors
SHALL be instances of `VndbError`.

#### Scenario: API errors share a base

- **WHEN** any HTTP error or network failure is raised by the client
- **THEN** the raised exception is an instance of `VndbError`

#### Scenario: API error carries status and message

- **WHEN** an API error is raised from a non-2xx response
- **THEN** the exception exposes the HTTP status code and the response body message

### Requirement: HTTP status mapping

The sans-I/O core SHALL map HTTP status codes to exception types: 400 to a
bad-request error, 401 to an authentication error, 404 to a not-found error, 429 to
a rate-limit error, and 5xx to a server error. It SHALL read the error message from
the response's plain-text body rather than assuming a JSON body.

#### Scenario: Map known status codes

- **WHEN** the status mapper is given status 400, 401, 404, 429, or a 5xx code with
  a plain-text body
- **THEN** it raises the corresponding exception subclass with the body text as the
  message

#### Scenario: Wrap network failures

- **WHEN** an httpx transport or timeout error occurs and retries are exhausted (or
  the error is non-retryable)
- **THEN** the client raises the network-error type wrapping the original exception
