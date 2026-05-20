# Fault Detection Service
# Evaluerer telemetridata og identificerer fejltilstande


class FaultDetectionService:

    MIN_VOLTAGE_V = 180.0
    MAX_CURRENT_A = 32.0

    def evaluate(self, charger_id, connector_id, status,
                 voltage_v, current_a, error_code=None):
        """
        Evaluer telemetridata mod domæneregler.
        Returnerer dict med fault_code og priority hvis fejl findes, ellers None.
        """
        fault_code = self._detect_fault(status, voltage_v, current_a, error_code)

        if fault_code is None:
            return None

        return {
            "fault_code": fault_code,
            "priority": self._determine_priority(fault_code)
        }

    def _detect_fault(self, status, voltage_v, current_a, error_code):
        # Regel 1: Ladestander rapporterer fejlstatus
        if status == "faulted":
            return self._classify_error_code(error_code)

        # Regel 2: Ladestander er offline
        if status == "offline":
            return "communication_error"

        # Regel 3: Spændingsfald
        if voltage_v < self.MIN_VOLTAGE_V:
            return "undervoltage"

        # Regel 4: Overstrøm
        if current_a > self.MAX_CURRENT_A:
            return "overcurrent"

        return None

    def _classify_error_code(self, error_code):
        if not error_code:
            return "unknown_fault"

        mapping = {
            "ConnectorLockFailure": "connector_lock_failure",
            "GroundFailure":        "ground_failure",
            "OverCurrentFailure":   "overcurrent",
            "UnderVoltage":         "undervoltage",
            "OverVoltage":          "overheat",
        }
        return mapping.get(error_code, "unknown_fault")

    def _determine_priority(self, fault_code):
        if fault_code in ("overcurrent", "ground_failure", "overheat"):
            return "high"
        if fault_code in ("undervoltage", "connector_lock_failure", "communication_error"):
            return "medium"
        return "low"
