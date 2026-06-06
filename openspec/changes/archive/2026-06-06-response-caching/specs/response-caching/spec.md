## ADDED Requirements

### Requirement: Opt-in response cache

The client SHALL support an opt-in in-memory response cache, enabled by a
`cache_ttl` argument on `Client` and `AsyncClient` (with an optional
`cache_maxsize`). When `cache_ttl` is unset (the default) or non-positive, no
caching SHALL occur and behavior is unchanged.

#### Scenario: Caching disabled by default
- **WHEN** a client is constructed without `cache_ttl`
- **THEN** every read issues a network request (no cache is consulted)

#### Scenario: Repeated read served from cache
- **WHEN** a client is constructed with `cache_ttl` set and the same read query is
  issued twice within the TTL
- **THEN** only the first issues a network request and the second is served from
  the cache

### Requirement: Cache scope and key

The cache SHALL key entries by the request's method, path, JSON body, and params,
and SHALL be scoped per client so that responses are not shared across clients
(and therefore not across tokens). Distinct queries SHALL map to distinct keys.

#### Scenario: Distinct queries are not conflated
- **WHEN** two reads differ in their filters/fields/params or path
- **THEN** they use different cache entries (a second distinct query is not served
  the first query's cached response)

### Requirement: Writes bypass the cache

Write requests (`PATCH`/`DELETE`) SHALL NOT be served from or stored in the cache;
they always issue a network request. Only read requests (`GET`/`POST`) are
cacheable, and only successful responses are stored.

#### Scenario: Write always hits the network
- **WHEN** a cache is enabled and a write (`PATCH`/`DELETE`) is issued, even
  repeatedly
- **THEN** each write issues a network request and no cache entry is created for it

#### Scenario: Errors are not cached
- **WHEN** a read returns an error status
- **THEN** no cache entry is stored for that request

### Requirement: TTL expiry and bounded size

Cached entries SHALL expire after `cache_ttl` seconds, after which the next
identical read refetches. The cache SHALL be bounded by `cache_maxsize`, evicting
least-recently-used entries beyond the bound.

#### Scenario: Refetch after expiry
- **WHEN** an identical read is issued after the cached entry's TTL has elapsed
- **THEN** a fresh network request is issued and the cache is repopulated

#### Scenario: Bounded by maxsize
- **WHEN** more distinct reads are cached than `cache_maxsize`
- **THEN** the least-recently-used entries are evicted to stay within the bound
