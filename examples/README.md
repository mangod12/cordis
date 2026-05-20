# Example Scenarios

Replayable crisis scenarios for testing and demonstration.

## Usage

```bash
# Start the server
make run

# Run a specific scenario
curl -X POST http://localhost:8000/process-emergency \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @examples/scenarios/warehouse_fire.json

# Or use the built-in demo commands
make demo-fire
make demo-flood
make demo-all
```

## Scenarios

| File | Type | Severity | What It Tests |
|------|------|----------|---------------|
| `warehouse_fire.json` | Triage | Critical/High | Fire dispatch + logistics trigger |
| `odisha_flood.json` | Logistics | Critical | Resource planning + route replanning |
| `chennai_cyclone.json` | Logistics | Critical | Airport/port fallback routing |
| `uttarakhand_earthquake.json` | Logistics | Critical | Multi-modal transport + SAR |
| `mumbai_stampede.json` | Triage | Critical | Mass casualty medical dispatch |

## Adding New Scenarios

Create a JSON file with:
```json
{
  "name": "Scenario Name",
  "description": "What this tests",
  "request": {
    "method": "POST",
    "endpoint": "/process-emergency",
    "body": { "transcript": "..." }
  },
  "expected_response": {
    "severity": "critical"
  }
}
```
