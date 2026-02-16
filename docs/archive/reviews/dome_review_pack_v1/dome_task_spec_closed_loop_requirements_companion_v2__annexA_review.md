---

## Annex A. Review Feedback (2026-02-16)
### Overall
- Requirements list is directionally correct; biggest value-add now is **traceability and verification**.

### Recommended adjustments
1. **Requirement IDs + verification method**
   - Add IDs (e.g., CL-REQ-001) and a “How verified” column/line (unit test / integration test / CI gate / audit query).
2. **Authoritative evidence store vs telemetry export**
   - If OpenTelemetry is used as “evidence,” explicitly require:
     - no sampling for control events
     - immutability/retention guarantees
     - replay-safe retrieval (consistent ordering/identity)
   - Alternatively: define a small event/history store as authoritative, and export to OTel for observability.
3. **Schema evolution policy**
   - Document compatibility rules (serve N-1, conversions, deprecation windows).
4. **Error taxonomy**
   - Define standard error codes/classes for tool failures, schema failures, policy failures, and timeout/retry outcomes.
