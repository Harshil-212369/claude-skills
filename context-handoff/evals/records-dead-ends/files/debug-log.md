Goal: flaky test tests/test_scheduler.py::test_fires_on_time fails ~1 in 5 runs on CI, never locally.
1. Tried increasing the sleep from 0.1s to 0.5s — still flaky on CI (failed 2/10). Reverted.
2. Tried pinning freezegun 1.5.1 — no change; freezegun doesn't patch the monotonic clock our scheduler uses. Reverted.
3. Found scheduler uses time.monotonic(); CI runners are 2-core and the event loop is starved. Switched the test to inject a fake clock (FakeClock in tests/conftest.py). Ran 50x locally: 50/50 pass.
4. Haven't run it on CI yet. Branch: fix/scheduler-flake, commit a1b2c3d.
5. Claude suggested also adding pytest-rerunfailures as a safety net. Not decided — I don't love masking flakes.
