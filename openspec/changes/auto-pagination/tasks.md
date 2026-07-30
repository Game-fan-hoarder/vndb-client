## 1. Pure pagination decision helper

- [x] 1.1 Add a frozen `PageWalk` dataclass to `src/vndb_client/core.py`, placed
      beside `RetryPolicy`, holding the starting page and the optional record cap,
      with a docstring stating it performs no I/O
- [x] 1.2 Implement the record-budget method answering how many of a page's
      records to keep, given the count already emitted and the count the API
      returned for this page
- [x] 1.3 Implement the continue/stop method covering all three termination
      conditions: the API reports no further pages, the cap is exhausted, or the
      page returned zero records while reporting further pages exist
- [x] 1.4 Validate construction: raise `ValueError` for a starting page below 1 or
      a cap of zero or below
- [x] 1.5 Add `tests/test_core.py` cases for `PageWalk` with no HTTP: budget
      arithmetic including the exact-boundary case, each termination condition
      independently, and both `ValueError` paths
- [x] 1.6 Confirm `PageWalk` stays out of `src/vndb_client/__init__.py`, mirroring
      `RetryPolicy` which is also internal, and verify `tests/test_public_api.py`
      needs no change

## 2. Synchronous pagination

- [x] 2.1 Add `QueryResource.pages()` in `src/vndb_client/resource.py` as a
      generator taking `query()`'s parameters except `page`, plus `start_page`,
      `limit`, and a page size defaulting to 100; delegate every stop/truncate
      decision to `PageWalk`
- [x] 2.2 Truncate a capped final page via `model_copy` with a sliced `results`
      list, leaving the API's `more` value intact
- [x] 2.3 Add `QueryResource.iterate()` as a generator delegating to `pages()` and
      yielding records, with no independent paging logic
- [x] 2.4 Write Google-style docstrings for both methods covering the cap's
      record semantics, `start_page` as the resumption point, the default page
      size, and that page size is not validated client-side
- [x] 2.5 Add `tests/test_resource.py` cases for the sync methods: multi-page walk
      terminating on `more=False`; incrementing page numbers and the `results=100`
      default in the issued requests; caller-supplied page size honoured; cap
      truncating mid-page with an exact record total; truncated page retaining
      `more=True`; `start_page` resumption; empty-page-with-`more=True` guard;
      laziness (no request until first iteration); error propagation mid-walk

## 3. Asynchronous pagination

- [x] 3.1 Add `AsyncQueryResource.pages()` as an async generator mirroring the
      sync signature and semantics, reusing the same `PageWalk`
- [x] 3.2 Add `AsyncQueryResource.iterate()` as an async generator delegating to
      the async `pages()`
- [x] 3.3 Mirror the docstrings from the sync methods
- [x] 3.4 Add async equivalents of every behavioural case in task 2.5, using the
      existing mocked-httpx async harness

## 4. Documentation

- [x] 4.1 Rewrite the pagination section of `docs/guides/querying.md` so
      `iterate()` is the recommended default, replacing the hand-rolled
      `while True` loop
- [x] 4.2 Add a `pages()` example showing envelope access for progress reporting
      against `page.count`
- [x] 4.3 Document the cap and `start_page`, including resuming a long walk after
      a rate-limit failure alongside a raised `RetryConfig.max_attempts`
- [x] 4.4 Document the three interactions: response-cache eviction during long
      walks (`cache_maxsize` default 128), `count` being returned on every page
      when requested, and the absence of snapshot consistency

## 5. Verification

- [x] 5.1 Run `make test` and confirm the suite passes with the new cases covering
      both sync and async paths
- [x] 5.2 Run `make check` and confirm the lock-file, ruff, mypy, and deptry gates
      pass, including full type annotations on the new generator signatures
- [x] 5.3 Run `make docs-test` and confirm the strict docs build stays clean after
      the guide rewrite
