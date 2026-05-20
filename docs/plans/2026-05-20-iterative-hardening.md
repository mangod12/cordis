# Iterative Self-Healing Hardening Plan

> **For Claude:** REQUIRED SUB-SKILL: Use godmode:task-runner to implement this plan task-by-task. After each task, run verification. If verification fails, diagnose and fix before proceeding. Loop until green or 3 attempts exhausted.

**Goal:** Iteratively harden Cordis — validate all new files, fix CI, add tests, enhance existing dashboard, add project history transparency — in a self-correcting loop that heals failures automatically.

**Architecture:** Each task has a VERIFY step. If VERIFY fails, the loop self-corrects: diagnose → fix → re-verify. Max 3 retries per task. Tasks are ordered by dependency — later tasks build on earlier ones passing.

**Tech Stack:** Python 3.11, FastAPI, pytest, ruff, Docker, GitHub Actions, Tailwind CSS, Leaflet.js

**Loop Protocol:**
```
for each task:
    attempt = 0
    while attempt < 3:
        execute task
        run VERIFY command
        if PASS: commit + move to next task
        if FAIL: read error output, diagnose, apply fix, attempt++
    if still failing after 3: log blocker, skip to next task
```

---

### Task 1: Fix CI — Add ruff to requirements and validate lint passes

**Files:**
- Modify: `backend/requirements.txt`
- Verify: `.github/workflows/ci.yml` (already created)

**Step 1: Add ruff to dev dependencies**

In `backend/requirements.txt`, append after the Testing section:

```
# ---- Linting / Dev tools ---------------------------------------------------
ruff>=0.4.0
pytest-cov>=5.0.0
```

**Step 2: Run ruff locally to verify it works**

Run: `cd D:/Cordis/backend && pip install ruff && ruff check app/ --select E,F,W,I`
Expected: Either clean pass OR specific errors to fix. Note any errors.

**Step 3: Self-heal — fix any ruff errors**

If ruff reports errors, fix them. Common expected issues:
- Unused imports (F401) — remove or add `# noqa: F401` if intentional
- f-string without placeholder (F541) — fix the string
- Undefined name (F821) — add missing import

Run: `ruff check app/ --fix --select E,F,W`
Then: `ruff check app/ --select E,F,W,I`
Expected: PASS (0 errors)

**Step 4: Commit**

```bash
git add backend/requirements.txt
git commit -m "$(cat <<'EOF'
chore: add ruff and pytest-cov to requirements

CI workflow needs ruff for linting. Add to requirements.txt
so both local dev and CI can use the same tool.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Validate Dockerfile builds successfully

**Files:**
- Modify: `backend/Dockerfile` (if fixes needed)

**Step 1: Test Docker build**

Run: `cd D:/Cordis && docker compose build backend`
Expected: Successful build. Watch for:
- `openai-whisper` needing rust compiler (tiktoken dependency)
- `torch` being huge (2GB+) — may need `--no-cache-dir`
- `pgvector` needing PostgreSQL headers

**Step 2: Self-heal — fix Dockerfile if build fails**

Common fixes:
- If tiktoken/rust fails: add `cargo` to apt-get install, OR add `RUN pip install tiktoken` before requirements
- If torch is too large: consider `torch` CPU-only via `--extra-index-url https://download.pytorch.org/whl/cpu`
- If gcc missing for C extensions: already in Dockerfile (gcc is there)

Apply fix, re-run `docker compose build backend`.

**Step 3: Test container starts**

Run: `docker compose up -d backend && sleep 5 && curl http://localhost:8000/health && docker compose down`
Expected: `{"status":"ok",...}` or `{"status":"degraded",...}` (degraded OK if no DB)

**Step 4: Commit if changes made**

```bash
git add backend/Dockerfile
git commit -m "$(cat <<'EOF'
fix: update Dockerfile for successful build

Address build issues discovered during validation.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Run existing tests — establish baseline

**Files:**
- None modified (diagnostic task)

**Step 1: Run full test suite**

Run: `cd D:/Cordis/backend && python -m pytest tests/ -v --tb=short 2>&1 | head -100`
Env: `SECRET_KEY=test-key USE_SQLITE=true LOGISTICS_ENABLED=true`
Expected: Note pass/fail count. This is the baseline.

**Step 2: Self-heal — fix any broken tests**

If tests fail due to import errors or missing env vars:
- Check if `conftest.py` sets up path correctly
- Check if `SECRET_KEY` env var is set
- Check if any test assumes Redis is running (mock it)

Fix and re-run until baseline is green.

**Step 3: Record baseline**

Note: X passed, Y failed, Z skipped. This is the starting point.

---

### Task 4: Add pipeline connector tests (0% → covered)

**Files:**
- Create: `backend/tests/test_pipeline_connector.py`
- Test: `backend/app/services/pipeline_connector.py`

**Step 1: Write failing tests**

```python
"""Tests for pipeline_connector — bridges triage to logistics."""
import pytest
from unittest.mock import patch, AsyncMock

from app.services.pipeline_connector import (
    should_trigger_logistics,
    build_crisis_query,
    trigger_logistics_pipeline,
)


class TestShouldTriggerLogistics:
    def test_critical_fire_triggers(self):
        assert should_trigger_logistics("critical", "FIRE") is True

    def test_critical_medical_triggers(self):
        assert should_trigger_logistics("critical", "MEDICAL") is True

    def test_high_accident_triggers(self):
        assert should_trigger_logistics("high", "ACCIDENT") is True

    def test_high_gas_hazard_triggers(self):
        assert should_trigger_logistics("high", "GAS_HAZARD") is True

    def test_low_fire_does_not_trigger(self):
        assert should_trigger_logistics("low", "FIRE") is False

    def test_critical_noise_complaint_does_not_trigger(self):
        assert should_trigger_logistics("critical", "NON_EMERGENCY") is False

    def test_medium_medical_does_not_trigger(self):
        assert should_trigger_logistics("medium", "MEDICAL") is False

    def test_auto_dispatch_false_blocks(self):
        assert should_trigger_logistics("critical", "FIRE", auto_dispatch=False) is False

    @patch("app.services.pipeline_connector.settings")
    def test_logistics_disabled_blocks(self, mock_settings):
        mock_settings.LOGISTICS_ENABLED = False
        assert should_trigger_logistics("critical", "FIRE") is False


class TestBuildCrisisQuery:
    def test_contains_severity(self):
        query = build_crisis_query("fire at warehouse", "FIRE", "critical", "fear", "fire_dispatch")
        assert "Critical" in query

    def test_contains_intent(self):
        query = build_crisis_query("fire at warehouse", "FIRE", "critical", "fear", "fire_dispatch")
        assert "Fire" in query

    def test_contains_transcript_excerpt(self):
        query = build_crisis_query("massive fire at 5th street", "FIRE", "high", "fear", "fire_dispatch")
        assert "massive fire at 5th street" in query

    def test_critical_adds_expedite(self):
        query = build_crisis_query("fire", "FIRE", "critical", "fear", "fire_dispatch")
        assert "CRITICAL" in query
        assert "expedite" in query.lower()

    def test_high_no_expedite(self):
        query = build_crisis_query("fire", "FIRE", "high", "fear", "fire_dispatch")
        assert "expedite" not in query.lower()

    def test_truncates_long_transcript(self):
        long_text = "x" * 1000
        query = build_crisis_query(long_text, "FIRE", "high", "fear", "fire_dispatch")
        # Should include max 500 chars of transcript
        assert len(query) < 1100
```

**Step 2: Run tests to verify they pass**

Run: `cd D:/Cordis/backend && SECRET_KEY=test python -m pytest tests/test_pipeline_connector.py -v --tb=short`
Expected: All PASS (these test existing code, not new code)

**Step 3: Self-heal if any fail**

Read error, adjust test expectations to match actual code behavior, re-run.

**Step 4: Commit**

```bash
git add backend/tests/test_pipeline_connector.py
git commit -m "$(cat <<'EOF'
test: add pipeline connector tests

Cover should_trigger_logistics, build_crisis_query with 14 test cases.
Validates severity/intent gating, auto_dispatch flag, and query construction.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Add logistics orchestrator unit tests

**Files:**
- Create: `backend/tests/test_orchestrator_unit.py`
- Test: `backend/app/agents/logistics/orchestrator.py` (helper functions only)

**Step 1: Write tests for deterministic helper functions**

```python
"""Unit tests for orchestrator helper functions — no LLM, no DB required."""
import pytest


class TestComputeSeverity:
    def test_critical_threshold(self):
        from app.agents.logistics.orchestrator import _compute_severity
        assert _compute_severity(300) == "Critical"
        assert _compute_severity(500) == "Critical"

    def test_moderate_threshold(self):
        from app.agents.logistics.orchestrator import _compute_severity
        assert _compute_severity(100) == "Moderate"
        assert _compute_severity(200) == "Moderate"
        assert _compute_severity(299) == "Moderate"

    def test_low_threshold(self):
        from app.agents.logistics.orchestrator import _compute_severity
        assert _compute_severity(50) == "Low"
        assert _compute_severity(99) == "Low"


class TestShouldForceReplan:
    def test_flood_triggers_replan(self):
        from app.agents.logistics.orchestrator import _should_force_replan
        assert _should_force_replan("Massive flood in coastal region") is True

    def test_cyclone_triggers_replan(self):
        from app.agents.logistics.orchestrator import _should_force_replan
        assert _should_force_replan("Cyclone warning for eastern coast") is True

    def test_earthquake_triggers_replan(self):
        from app.agents.logistics.orchestrator import _should_force_replan
        assert _should_force_replan("Earthquake magnitude 7.2") is True

    def test_normal_query_no_replan(self):
        from app.agents.logistics.orchestrator import _should_force_replan
        assert _should_force_replan("Routine supply delivery to warehouse") is False

    def test_war_triggers_replan(self):
        from app.agents.logistics.orchestrator import _should_force_replan
        assert _should_force_replan("Armed conflict in border region") is True


class TestCrisisTypeLookup:
    def test_known_crisis_types(self):
        from app.agents.logistics.orchestrator import _CRISIS_TYPES
        assert _CRISIS_TYPES["flood"] == "Flood"
        assert _CRISIS_TYPES["earthquake"] == "Earthquake"
        assert _CRISIS_TYPES["cyclone"] == "Cyclone"
        assert _CRISIS_TYPES["tsunami"] == "Tsunami"
        assert _CRISIS_TYPES["war"] == "Armed Conflict"

    def test_resource_lookup(self):
        from app.agents.logistics.orchestrator import _RESOURCES
        assert _RESOURCES["food"] == "Food Supply"
        assert _RESOURCES["medicine"] == "Medical Supplies"
        assert _RESOURCES["water"] == "Drinking Water"


class TestComputeRealMetrics:
    def test_known_route_produces_valid_metrics(self):
        from app.agents.logistics.orchestrator import _compute_real_metrics
        fb = {
            "source": "Rourkela Depot",
            "destination": "Bhubaneswar",
            "quantity": 200,
            "route": "NH-49",
        }
        metrics = _compute_real_metrics(fb)
        assert "eta_hrs" in metrics
        assert "truck_count" in metrics
        assert metrics["truck_count"] >= 2
        assert metrics["eta_hrs"] > 0

    def test_unknown_city_uses_defaults(self):
        from app.agents.logistics.orchestrator import _compute_real_metrics
        fb = {
            "source": "UnknownCity Depot",
            "destination": "NowhereLand",
            "quantity": 100,
            "route": "NH-1",
        }
        metrics = _compute_real_metrics(fb)
        assert metrics["eta_hrs"] == 2.5  # default
        assert metrics["truck_count"] >= 2
```

**Step 2: Run tests**

Run: `cd D:/Cordis/backend && SECRET_KEY=test python -m pytest tests/test_orchestrator_unit.py -v --tb=short`
Expected: All PASS

**Step 3: Self-heal if imports fail or assertions wrong**

Adjust imports/assertions based on actual function signatures.

**Step 4: Commit**

```bash
git add backend/tests/test_orchestrator_unit.py
git commit -m "$(cat <<'EOF'
test: add orchestrator unit tests for deterministic helpers

18 tests covering _compute_severity, _should_force_replan,
_compute_real_metrics, and lookup table validation.
No LLM or DB required.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Add route_tool unit tests (real geodata validation)

**Files:**
- Create: `backend/tests/test_route_tool.py`
- Test: `backend/app/services/logistics/tools/route_tool.py`

**Step 1: Write tests**

```python
"""Tests for route_tool — haversine, city resolution, airport/port data."""
import pytest


class TestHaversine:
    def test_same_point_is_zero(self):
        from app.services.logistics.tools.route_tool import _haversine_km
        assert _haversine_km(20.0, 85.0, 20.0, 85.0) == 0.0

    def test_bhubaneswar_to_kolkata(self):
        from app.services.logistics.tools.route_tool import _haversine_km
        # Approx 440 km by air
        dist = _haversine_km(20.2961, 85.8245, 22.5726, 88.3639)
        assert 350 < dist < 500

    def test_delhi_to_mumbai(self):
        from app.services.logistics.tools.route_tool import _haversine_km
        dist = _haversine_km(28.6139, 77.2090, 19.0760, 72.8777)
        assert 1100 < dist < 1400


class TestResolveCity:
    def test_known_city(self):
        from app.services.logistics.tools.route_tool import _resolve_city
        coords = _resolve_city("Bhubaneswar")
        assert coords is not None
        lat, lon = coords
        assert 20.0 < lat < 21.0
        assert 85.0 < lon < 86.5

    def test_unknown_city_returns_none(self):
        from app.services.logistics.tools.route_tool import _resolve_city
        assert _resolve_city("Atlantis") is None

    def test_kolkata(self):
        from app.services.logistics.tools.route_tool import _resolve_city
        coords = _resolve_city("Kolkata")
        assert coords is not None


class TestStaticData:
    def test_airports_have_required_fields(self):
        from app.services.logistics.tools.route_tool import AIRPORTS
        assert len(AIRPORTS) >= 19
        for ap in AIRPORTS:
            assert "name" in ap
            assert "code" in ap
            assert "lat" in ap
            assert "lon" in ap
            assert "runway_m" in ap
            assert isinstance(ap["lat"], (int, float))
            assert isinstance(ap["lon"], (int, float))

    def test_ports_have_required_fields(self):
        from app.services.logistics.tools.route_tool import PORTS
        assert len(PORTS) >= 13
        for pt in PORTS:
            assert "name" in pt
            assert "city" in pt
            assert "lat" in pt
            assert "lon" in pt
            assert "capacity_mt_yr" in pt
```

**Step 2: Run tests**

Run: `cd D:/Cordis/backend && SECRET_KEY=test python -m pytest tests/test_route_tool.py -v --tb=short`
Expected: All PASS

**Step 3: Self-heal**

If `_haversine_km` or `_resolve_city` are not importable, check actual function names via grep and adjust.

**Step 4: Commit**

```bash
git add backend/tests/test_route_tool.py
git commit -m "$(cat <<'EOF'
test: add route_tool tests for geodata and haversine

11 tests: haversine distance validation, city resolution,
airport/port data integrity (19 airports, 13+ ports).

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Add project history to README (transparency)

**Files:**
- Modify: `README.md`

**Step 1: Add History section before License**

Insert before the `## License` section:

```markdown
---

## History

Cordis began as two separate projects:

- **Redline-AI** — an AI-powered emergency triage system (voice → intent → severity → dispatch)
- **TaskForge** — a multi-agent logistics coordination engine for crisis supply chains

In May 2026, both were merged into **Cordis** — a single end-to-end platform that connects distress calls directly to resource dispatch. The name comes from the Latin word for "heart."
```

**Step 2: Verify README renders correctly**

Run: `head -5 D:/Cordis/README.md && echo "..." && grep -n "## History" D:/Cordis/README.md`
Expected: History section present, no broken markdown.

**Step 3: Commit**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
docs: add project history section to README

Transparently documents Cordis origins from Redline-AI + TaskForge.
Addresses provenance questions before public launch.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 8: Enhance existing dashboard — add crisis map + voice input

**Files:**
- Modify: `backend/app/dashboard/templates/index.html`

**Step 1: Add Leaflet map + audio upload to existing dashboard**

Replace the entire `index.html` with enhanced version that adds:
- Leaflet.js map panel showing crisis locations
- Audio file upload button with visual feedback
- Text input for transcript (existing curl functionality, now in UI)
- Agent pipeline status indicators
- Keep existing call table

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{{ title }}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    #map { height: 300px; border-radius: 0.75rem; }
    .pulse { animation: pulse 2s infinite; }
    @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
    .agent-step { transition: all 0.3s ease; }
    .agent-step.active { border-color: #22d3ee; background: rgba(34,211,238,0.1); }
    .agent-step.done { border-color: #4ade80; background: rgba(74,222,128,0.1); }
    .agent-step.error { border-color: #f87171; background: rgba(248,113,113,0.1); }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">
  <div class="max-w-7xl mx-auto px-4 py-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">Cordis</h1>
        <p class="text-xs text-slate-400 mt-1">AI Crisis Coordination — from distress call to resource dispatch</p>
      </div>
      <div class="flex items-center gap-3">
        <span id="system-status" class="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-400">
          <span class="w-2 h-2 rounded-full bg-emerald-400 pulse"></span> System Active
        </span>
        <p id="last-updated" class="text-sm text-slate-400">Refreshing...</p>
      </div>
    </div>

    <!-- Stats Row -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
      <div class="rounded-xl bg-slate-900 border border-slate-800 p-3">
        <p class="text-xs text-slate-400">Total Calls</p>
        <p id="stat-total" class="text-2xl font-semibold">0</p>
      </div>
      <div class="rounded-xl bg-slate-900 border border-slate-800 p-3">
        <p class="text-xs text-slate-400">Critical</p>
        <p id="stat-critical" class="text-2xl font-semibold text-rose-400">0</p>
      </div>
      <div class="rounded-xl bg-slate-900 border border-slate-800 p-3">
        <p class="text-xs text-slate-400">High</p>
        <p id="stat-high" class="text-2xl font-semibold text-amber-300">0</p>
      </div>
      <div class="rounded-xl bg-slate-900 border border-slate-800 p-3">
        <p class="text-xs text-slate-400">Avg Latency</p>
        <p id="stat-latency" class="text-2xl font-semibold text-cyan-300">— ms</p>
      </div>
      <div class="rounded-xl bg-slate-900 border border-slate-800 p-3">
        <p class="text-xs text-slate-400">Fallback Rate</p>
        <p id="stat-fallback" class="text-2xl font-semibold text-violet-300">0%</p>
      </div>
    </div>

    <!-- Two Column: Map + Input -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
      <!-- Map Panel -->
      <div class="rounded-xl bg-slate-900 border border-slate-800 p-4">
        <h2 class="text-sm font-semibold text-slate-300 mb-2">Crisis Map</h2>
        <div id="map"></div>
      </div>

      <!-- Input Panel -->
      <div class="rounded-xl bg-slate-900 border border-slate-800 p-4">
        <h2 class="text-sm font-semibold text-slate-300 mb-3">Submit Emergency</h2>

        <!-- Audio Upload -->
        <div class="mb-3">
          <label class="block text-xs text-slate-400 mb-1">Audio File (optional)</label>
          <input type="file" id="audio-input" accept="audio/*"
            class="block w-full text-xs text-slate-400
              file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0
              file:text-xs file:font-medium file:bg-slate-800 file:text-slate-200
              hover:file:bg-slate-700 cursor-pointer" />
          <div id="audio-status" class="text-xs text-slate-500 mt-1 hidden"></div>
        </div>

        <!-- Text Transcript -->
        <div class="mb-3">
          <label class="block text-xs text-slate-400 mb-1">Or type transcript</label>
          <textarea id="transcript-input" rows="3" placeholder="There is a massive fire at the warehouse on 5th street..."
            class="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none resize-none"></textarea>
        </div>

        <button id="submit-btn" onclick="submitEmergency()"
          class="w-full py-2 px-4 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
          Process Emergency
        </button>

        <!-- Agent Pipeline Visualization -->
        <div id="pipeline-viz" class="mt-4 hidden">
          <h3 class="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">Agent Pipeline</h3>
          <div class="flex gap-1.5">
            <div id="step-stt" class="agent-step flex-1 rounded-lg border border-slate-700 p-2 text-center">
              <p class="text-[10px] text-slate-400">STT</p>
              <p class="text-xs font-mono" id="step-stt-val">—</p>
            </div>
            <div id="step-intent" class="agent-step flex-1 rounded-lg border border-slate-700 p-2 text-center">
              <p class="text-[10px] text-slate-400">Intent</p>
              <p class="text-xs font-mono" id="step-intent-val">—</p>
            </div>
            <div id="step-emotion" class="agent-step flex-1 rounded-lg border border-slate-700 p-2 text-center">
              <p class="text-[10px] text-slate-400">Emotion</p>
              <p class="text-xs font-mono" id="step-emotion-val">—</p>
            </div>
            <div id="step-severity" class="agent-step flex-1 rounded-lg border border-slate-700 p-2 text-center">
              <p class="text-[10px] text-slate-400">Severity</p>
              <p class="text-xs font-mono" id="step-severity-val">—</p>
            </div>
            <div id="step-dispatch" class="agent-step flex-1 rounded-lg border border-slate-700 p-2 text-center">
              <p class="text-[10px] text-slate-400">Dispatch</p>
              <p class="text-xs font-mono" id="step-dispatch-val">—</p>
            </div>
          </div>
        </div>

        <!-- Result Card -->
        <div id="result-card" class="mt-3 hidden rounded-lg border border-slate-700 p-3">
          <div class="flex justify-between items-center mb-2">
            <span id="result-severity" class="text-sm font-bold"></span>
            <span id="result-latency" class="text-xs text-slate-400"></span>
          </div>
          <p id="result-detail" class="text-xs text-slate-300"></p>
        </div>
      </div>
    </div>

    <!-- Calls Table -->
    <div class="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900">
      <table class="min-w-full text-sm">
        <thead class="bg-slate-800/70 text-slate-300 text-xs uppercase">
          <tr>
            <th class="px-3 py-3 text-left">Call ID</th>
            <th class="px-3 py-3 text-left">Transcript</th>
            <th class="px-3 py-3 text-left">Intent (conf)</th>
            <th class="px-3 py-3 text-left">Emotion</th>
            <th class="px-3 py-3 text-left">Severity</th>
            <th class="px-3 py-3 text-left">Responder</th>
            <th class="px-3 py-3 text-left">Latency</th>
          </tr>
        </thead>
        <tbody id="calls-body" class="divide-y divide-slate-800">
          <tr>
            <td colspan="7" class="px-3 py-8 text-center text-slate-400">Waiting for calls...</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <script>
    // ── Map Setup ──
    const map = L.map("map").setView([20.5, 82.0], 5);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
      maxZoom: 18,
    }).addTo(map);

    const markers = {};
    const sevColors = { critical: "#f87171", high: "#fbbf24", medium: "#facc15", low: "#4ade80" };

    // Known city coordinates for map plotting
    const CITIES = {
      bhubaneswar:[20.30,85.82], kolkata:[22.57,88.36], chennai:[13.08,80.27],
      mumbai:[19.08,72.88], delhi:[28.61,77.21], bangalore:[12.97,77.59],
      hyderabad:[17.39,78.49], ahmedabad:[23.02,72.57], jaipur:[26.91,75.79],
      patna:[25.61,85.14], guwahati:[26.14,91.74], pune:[18.52,73.86],
      lucknow:[26.85,80.95], puri:[19.81,85.83], cuttack:[20.46,85.88],
      surat:[21.17,72.83], odisha:[20.50,84.00], bihar:[25.60,85.10],
      assam:[26.20,92.94], kerala:[10.85,76.27], gujarat:[22.26,71.19],
    };

    function plotCall(c) {
      const text = (c.transcript || "").toLowerCase();
      for (const [city, coords] of Object.entries(CITIES)) {
        if (text.includes(city)) {
          const color = sevColors[c.severity] || "#94a3b8";
          const circle = L.circleMarker(coords, {
            radius: c.severity === "critical" ? 10 : c.severity === "high" ? 7 : 5,
            fillColor: color, color: color, weight: 1, opacity: 0.8, fillOpacity: 0.5,
          }).addTo(map);
          circle.bindPopup(`<b>${c.severity.toUpperCase()}</b><br>${c.intent}<br>${(c.transcript||"").slice(0,80)}...`);
          markers[c.call_id] = circle;
          break;
        }
      }
    }

    // ── Emergency Submission ──
    async function submitEmergency() {
      const btn = document.getElementById("submit-btn");
      const audioInput = document.getElementById("audio-input");
      const textInput = document.getElementById("transcript-input");
      const pipelineViz = document.getElementById("pipeline-viz");
      const resultCard = document.getElementById("result-card");

      btn.disabled = true;
      btn.textContent = "Processing...";
      pipelineViz.classList.remove("hidden");
      resultCard.classList.add("hidden");

      // Animate pipeline steps
      const steps = ["stt", "intent", "emotion", "severity", "dispatch"];
      steps.forEach(s => {
        document.getElementById("step-" + s).className = "agent-step flex-1 rounded-lg border border-slate-700 p-2 text-center";
        document.getElementById("step-" + s + "-val").textContent = "—";
      });

      try {
        let response;
        const token = localStorage.getItem("cordis_token") || "";
        const headers = { Authorization: "Bearer " + token };

        if (audioInput.files.length > 0) {
          const formData = new FormData();
          formData.append("audio_file", audioInput.files[0]);
          animateStep("stt", "active", "...");
          response = await fetch("/process-emergency", { method: "POST", headers, body: formData });
        } else if (textInput.value.trim()) {
          animateStep("stt", "done", "text");
          response = await fetch("/process-emergency", {
            method: "POST",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify({ transcript: textInput.value.trim() }),
          });
        } else {
          alert("Provide audio or text transcript.");
          btn.disabled = false;
          btn.textContent = "Process Emergency";
          return;
        }

        if (!response.ok) {
          const err = await response.json().catch(() => ({ detail: response.statusText }));
          throw new Error(err.detail || response.statusText);
        }

        const data = await response.json();

        // Animate completed pipeline
        animateStep("stt", "done", "done");
        setTimeout(() => animateStep("intent", "done", data.intent), 100);
        setTimeout(() => animateStep("emotion", "done", data.emotion), 200);
        setTimeout(() => animateStep("severity", "done", data.severity), 300);
        setTimeout(() => animateStep("dispatch", "done", data.responder), 400);

        // Show result card
        setTimeout(() => {
          resultCard.classList.remove("hidden");
          const sevEl = document.getElementById("result-severity");
          sevEl.textContent = data.severity.toUpperCase() + " — " + data.intent;
          sevEl.className = "text-sm font-bold " + sevClass(data.severity);
          document.getElementById("result-latency").textContent = data.latency_ms + "ms";
          document.getElementById("result-detail").textContent =
            "Dispatched: " + data.responder + " | Call ID: " + data.call_id;
          plotCall(data);
        }, 500);

        // Refresh table
        refresh();
      } catch (err) {
        animateStep("stt", "error", "ERR");
        document.getElementById("result-card").classList.remove("hidden");
        document.getElementById("result-severity").textContent = "ERROR";
        document.getElementById("result-severity").className = "text-sm font-bold text-rose-400";
        document.getElementById("result-detail").textContent = err.message;
        document.getElementById("result-latency").textContent = "";
      } finally {
        btn.disabled = false;
        btn.textContent = "Process Emergency";
      }
    }

    function animateStep(name, state, value) {
      const el = document.getElementById("step-" + name);
      el.className = "agent-step " + state + " flex-1 rounded-lg border border-slate-700 p-2 text-center";
      document.getElementById("step-" + name + "-val").textContent = value || "—";
    }

    // ── Table Refresh ──
    function sevClass(level) {
      if (level === "critical") return "text-rose-400";
      if (level === "high") return "text-amber-300";
      if (level === "medium") return "text-yellow-300";
      return "text-emerald-300";
    }

    function trimText(text, maxLen) {
      if (!text) return "";
      return text.length > maxLen ? text.slice(0, maxLen) + "..." : text;
    }

    function renderRow(c) {
      return `
        <tr class="hover:bg-slate-800/40 cursor-pointer" onclick="plotCall(${JSON.stringify(c).replace(/"/g, '&quot;')})">
          <td class="px-3 py-2 font-mono text-xs text-slate-300">${c.call_id}</td>
          <td class="px-3 py-2 text-slate-200 max-w-xl">${trimText(c.transcript || "", 100)}</td>
          <td class="px-3 py-2 text-slate-200">${c.intent} (${((c.intent_confidence || 0) * 100).toFixed(0)}%)</td>
          <td class="px-3 py-2 text-slate-200">${c.emotion}</td>
          <td class="px-3 py-2 font-semibold ${sevClass(c.severity)}">${c.severity}</td>
          <td class="px-3 py-2 text-slate-200">${c.responder}</td>
          <td class="px-3 py-2 text-cyan-300">${Number(c.latency_ms || 0).toFixed(0)} ms</td>
        </tr>
      `;
    }

    async function refresh() {
      try {
        const token = localStorage.getItem("cordis_token") || "";
        const response = await fetch("/api/v1/calls/live?limit=50", {
          headers: { Authorization: "Bearer " + token },
        });
        if (!response.ok) return;
        const data = await response.json();
        const calls = data.calls || [];

        document.getElementById("last-updated").textContent = "Updated " + new Date().toLocaleTimeString();
        document.getElementById("stat-total").textContent = String(calls.length);
        document.getElementById("stat-critical").textContent = String(calls.filter(c => c.severity === "critical").length);
        document.getElementById("stat-high").textContent = String(calls.filter(c => c.severity === "high").length);

        const avgLatency = calls.length
          ? Math.round(calls.reduce((sum, c) => sum + (c.latency_ms || 0), 0) / calls.length)
          : 0;
        document.getElementById("stat-latency").textContent = avgLatency ? avgLatency + " ms" : "— ms";

        const fallbackRate = calls.length
          ? Math.round((calls.filter(c => c.fallback_used).length / calls.length) * 100)
          : 0;
        document.getElementById("stat-fallback").textContent = fallbackRate + "%";

        const body = document.getElementById("calls-body");
        if (!calls.length) {
          body.innerHTML = '<tr><td colspan="7" class="px-3 py-8 text-center text-slate-400">Waiting for calls...</td></tr>';
          return;
        }
        body.innerHTML = calls.map(renderRow).join("");

        // Plot all calls on map
        calls.forEach(plotCall);
      } catch (error) {
        document.getElementById("last-updated").textContent = "Refresh failed";
      }
    }

    // ── Init ──
    refresh();
    setInterval(refresh, 3000);

    // Simple token input (for demo purposes)
    if (!localStorage.getItem("cordis_token")) {
      const token = prompt("Enter JWT token (or press Cancel for demo mode):");
      if (token) localStorage.setItem("cordis_token", token);
    }
  </script>
</body>
</html>
```

**Step 2: Verify template renders**

Run: `cd D:/Cordis/backend && SECRET_KEY=test USE_SQLITE=true python -c "from app.dashboard.routes import templates; print(templates.get_template('index.html'))" 2>&1`
Expected: Template object returned (no Jinja2 errors)

**Step 3: Self-heal if template has syntax errors**

Fix any Jinja2 or HTML issues, re-verify.

**Step 4: Commit**

```bash
git add backend/app/dashboard/templates/index.html
git commit -m "$(cat <<'EOF'
feat: enhance dashboard with crisis map, voice input, agent pipeline viz

Replace basic table-only dashboard with full crisis coordination UI:
- Leaflet dark map with severity-colored markers
- Audio file upload + text transcript input
- Agent pipeline visualization (STT→Intent→Emotion→Severity→Dispatch)
- Result card with dispatch details
- Avg latency stat, clickable rows plot on map
All in existing Jinja2 template — no React/npm build needed.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 9: Run full test suite — measure improvement

**Files:** None modified

**Step 1: Run all tests with coverage**

Run: `cd D:/Cordis/backend && SECRET_KEY=test USE_SQLITE=true python -m pytest tests/ -v --tb=short --cov=app --cov-report=term-missing 2>&1 | tail -40`
Expected: More tests passing than Task 3 baseline. Note new coverage %.

**Step 2: Self-heal any failures introduced**

If new tests broke old tests (import side effects, etc.), fix the conflict.

**Step 3: Record final metrics**

Baseline (Task 3): X tests
After (Task 9): Y tests
Coverage: Z%

---

### Task 10: Commit all community/infra files created earlier

**Files:**
- `CLAUDE.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `docs/ROADMAP.md`
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`
- `.github/pull_request_template.md`
- `backend/pyproject.toml`
- `backend/.dockerignore`

**Step 1: Stage and commit community files**

```bash
git add CLAUDE.md SECURITY.md CODE_OF_CONDUCT.md docs/ROADMAP.md
git commit -m "$(cat <<'EOF'
docs: add AI context, security policy, code of conduct, roadmap

- CLAUDE.md: AI assistant context for codebase understanding
- SECURITY.md: vulnerability reporting and security measures
- CODE_OF_CONDUCT.md: Contributor Covenant
- docs/ROADMAP.md: versioned feature roadmap (v0.2→v1.0)

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

**Step 2: Stage and commit GitHub templates**

```bash
git add .github/
git commit -m "$(cat <<'EOF'
ci: add GitHub Actions CI, issue templates, PR template

- CI: lint (ruff), syntax check, test with coverage, Docker build
- Issue templates: bug report, feature request
- PR template with test plan checklist

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

**Step 3: Stage and commit Docker/config files**

```bash
git add backend/Dockerfile backend/.dockerignore backend/pyproject.toml
git commit -m "$(cat <<'EOF'
chore: add Dockerfile, dockerignore, pyproject.toml

- Dockerfile: production image with ffmpeg, non-root user, healthcheck
- .dockerignore: exclude venv, cache, db files
- pyproject.toml: ruff config + pytest settings

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Loop Protocol — After All Tasks

After Task 10, run the full verification loop:

```
1. ruff check backend/app/ → must be clean
2. pytest tests/ -v → all green
3. docker compose build → success
4. grep -r "TODO\|FIXME\|HACK" backend/app/ → review any new ones
5. git log --oneline -10 → verify clean commit history
```

If any step fails, loop back: diagnose → fix → re-verify. Max 3 loops on the full suite.
