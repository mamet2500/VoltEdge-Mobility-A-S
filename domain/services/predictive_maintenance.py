import logging

logger = logging.getLogger(__name__)

class PredictiveMaintenanceService:
    MIN_READINGS    = 5
    FAULT_RATE_HIGH = 0.20
    MIN_VOLTAGE_V   = 210.0
    MAX_CURRENT_A   = 28.0

    def analyse(self, connector_id, readings):
        if len(readings) < self.MIN_READINGS:
            return {"connector_id": connector_id, "risk_level": "low", "health_score": 1.0,
                    "reasons": ["Ikke nok data (minimum 5 maalinger)"],
                    "recommendation": "Fortsaet normal drift.", "readings_analysed": len(readings)}
        score = 0.0
        reasons = []
        fault_rate = self._fault_rate(readings)
        if fault_rate >= self.FAULT_RATE_HIGH:
            score += 0.40
            reasons.append(f"Hoej fejlrate: {fault_rate:.0%}")
        elif fault_rate >= 0.10:
            score += 0.20
            reasons.append(f"Moderat fejlrate: {fault_rate:.0%}")
        avg_voltage = self._avg_voltage(readings)
        if avg_voltage < 190.0:
            score += 0.25
            reasons.append(f"Kritisk lav spaending: {avg_voltage:.1f}V")
        elif avg_voltage < self.MIN_VOLTAGE_V:
            score += 0.12
            reasons.append(f"Lav spaending: {avg_voltage:.1f}V")
        avg_current = self._avg_current(readings)
        if avg_current > 30.0:
            score += 0.20
            reasons.append(f"Kritisk hoej stroem: {avg_current:.1f}A")
        elif avg_current > self.MAX_CURRENT_A:
            score += 0.10
            reasons.append(f"Hoej stroem: {avg_current:.1f}A")
        score = min(score, 1.0)
        health_score = round(1.0 - score, 2)
        risk_level = self._risk_level(score)
        logger.info("Predictive: connector=%s risk=%s health=%.2f", connector_id, risk_level, health_score)
        return {"connector_id": connector_id, "risk_level": risk_level, "health_score": health_score,
                "reasons": reasons if reasons else ["Ingen bekaymrende mønstre"],
                "recommendation": self._recommendation(risk_level), "readings_analysed": len(readings)}

    def _fault_rate(self, readings):
        return sum(1 for r in readings if r.get("status") in ("faulted","offline")) / len(readings)

    def _avg_voltage(self, readings):
        v = [r["voltage"] for r in readings if r.get("voltage") is not None]
        return sum(v)/len(v) if v else 230.0

    def _avg_current(self, readings):
        c = [r["current_amp"] for r in readings if r.get("current_amp") is not None]
        return sum(c)/len(c) if c else 0.0

    def _risk_level(self, score):
        if score >= 0.6: return "high"
        if score >= 0.3: return "medium"
        return "low"

    def _recommendation(self, risk_level):
        if risk_level == "high": return "Planlaeg vedligeholdelse snarest."
        if risk_level == "medium": return "Oget overvaagning anbefales inden for 7 dage."
        return "Ingen handling noedvendig."
