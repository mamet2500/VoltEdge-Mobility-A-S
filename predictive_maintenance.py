# Predictive Maintenance Service
# Analyserer historisk telemetri og forudsiger fejlrisiko


class PredictiveMaintenanceService:

    MIN_READINGS     = 5
    FAULT_RATE_HIGH  = 0.20
    MIN_VOLTAGE_V    = 210.0
    MAX_CURRENT_A    = 28.0

    def analyse(self, charger_id, readings):
        """
        Analysér telemetridata og returner en risikovurdering.
        readings: liste af dicts fra get_telemetry_by_charger()
        """
        if len(readings) < self.MIN_READINGS:
            return {
                "charger_id": charger_id,
                "risk_level": "low",
                "risk_score": 0.0,
                "reasons": ["Ikke nok data til analyse (minimum 5 målinger)"],
                "recommendation": "Fortsæt normal drift og afvent flere målinger.",
                "readings_analysed": len(readings)
            }

        score   = 0.0
        reasons = []

        # Feature 1: Fejlrate
        fault_rate = self._fault_rate(readings)
        if fault_rate >= self.FAULT_RATE_HIGH:
            score += 0.40
            reasons.append(f"Høj fejlrate: {fault_rate:.0%} af målinger er faulted/offline")
        elif fault_rate >= 0.10:
            score += 0.20
            reasons.append(f"Moderat fejlrate: {fault_rate:.0%} af målinger er faulted/offline")

        # Feature 2: Gennemsnitsspænding
        avg_voltage = self._avg_voltage(readings)
        if avg_voltage < 190.0:
            score += 0.25
            reasons.append(f"Kritisk lav gennemsnitsspænding: {avg_voltage:.1f}V")
        elif avg_voltage < self.MIN_VOLTAGE_V:
            score += 0.12
            reasons.append(f"Lav gennemsnitsspænding: {avg_voltage:.1f}V")

        # Feature 3: Gennemsnitsstrøm
        avg_current = self._avg_current(readings)
        if avg_current > 30.0:
            score += 0.20
            reasons.append(f"Kritisk høj gennemsnitsstrøm: {avg_current:.1f}A")
        elif avg_current > self.MAX_CURRENT_A:
            score += 0.10
            reasons.append(f"Høj gennemsnitsstrøm: {avg_current:.1f}A")

        # Feature 4: Nylige fejl
        recent_fault_rate = self._recent_fault_rate(readings)
        if recent_fault_rate > 0.30:
            score += 0.15
            reasons.append(f"Mange fejl i seneste målinger: {recent_fault_rate:.0%}")

        score      = min(score, 1.0)
        risk_level = self._risk_level(score)

        return {
            "charger_id":        charger_id,
            "risk_level":        risk_level,
            "risk_score":        round(score, 2),
            "reasons":           reasons if reasons else ["Ingen bekymrende mønstre fundet"],
            "recommendation":    self._recommendation(risk_level),
            "readings_analysed": len(readings)
        }

    def _fault_rate(self, readings):
        faulted = sum(1 for r in readings if r.get("status") in ("faulted", "offline"))
        return faulted / len(readings)

    def _avg_voltage(self, readings):
        voltages = [r["voltage_v"] for r in readings if r.get("voltage_v") is not None]
        return sum(voltages) / len(voltages) if voltages else 230.0

    def _avg_current(self, readings):
        currents = [r["current_a"] for r in readings if r.get("current_a") is not None]
        return sum(currents) / len(currents) if currents else 0.0

    def _recent_fault_rate(self, readings):
        recent_count = max(1, len(readings) // 5)
        recent       = readings[:recent_count]
        faulted      = sum(1 for r in recent if r.get("status") in ("faulted", "offline"))
        return faulted / len(recent)

    def _risk_level(self, score):
        if score >= 0.6:
            return "high"
        if score >= 0.3:
            return "medium"
        return "low"

    def _recommendation(self, risk_level):
        if risk_level == "high":
            return "Planlæg vedligeholdelse snarest. Send tekniker ud til inspektion."
        if risk_level == "medium":
            return "Øget overvågning anbefales. Planlæg inspektion inden for 7 dage."
        return "Ingen handling nødvendig. Fortsæt normal drift."
