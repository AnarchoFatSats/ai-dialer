#!/usr/bin/env python3
"""
AI Dialer KPI Synthetic Generator
==================================

Generates synthetic KPI data for testing and validation.
Emits both console lines and artifacts/kpis.json.

Usage:
    python scripts/audit/kpi_synthetics.py

KPI Targets:
- Answer Rate ≥ 18%
- Transfer Rate ≥ 9%
- AI Response Time P95 ≤ 800ms
- Cost per Transfer ≤ $0.14
"""

import json
import logging
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
ARTIFACTS_DIR = Path("artifacts")
KPI_TARGETS = {
    "answer_rate": 18.0,  # ≥ 18%
    "transfer_rate": 9.0,  # ≥ 9%
    "ai_response_time_p95": 800.0,  # ≤ 800ms
    "cost_per_transfer": 0.14,  # ≤ $0.14
}

class KPISyntheticGenerator:
    def __init__(self):
        self.start_time = datetime.now()

    def generate_synthetic_data(self) -> Dict[str, float]:
        """Generate synthetic KPI data."""
        # Generate realistic but varying data
        base_answer_rate = random.uniform(15, 25)  # Base around target
        base_transfer_rate = random.uniform(7, 15)  # Base around target
        base_response_time = random.uniform(600, 1200)  # Base around target
        base_cost = random.uniform(0.08, 0.25)  # Base around target

        # Add some realistic variation
        answer_rate = base_answer_rate + random.uniform(-2, 2)
        transfer_rate = base_transfer_rate + random.uniform(-1, 1)
        response_time = base_response_time + random.uniform(-100, 100)
        cost = base_cost + random.uniform(-0.02, 0.02)

        return {
            "answer_rate": max(0, min(100, answer_rate)),  # Clamp 0-100
            "transfer_rate": max(0, min(100, transfer_rate)),  # Clamp 0-100
            "ai_response_time_p95": max(100, response_time),  # Min 100ms
            "cost_per_transfer": max(0.01, cost),  # Min $0.01
            "generated_at": self.start_time.isoformat(),
            "data_quality": "synthetic"
        }

    def validate_kpis(self, kpis: Dict[str, float]) -> Dict[str, bool]:
        """Validate KPIs against targets."""
        results = {}

        for metric, target in KPI_TARGETS.items():
            if metric in kpis:
                actual = kpis[metric]
                if metric in ["answer_rate", "transfer_rate"]:
                    results[metric] = actual >= target
                else:
                    results[metric] = actual <= target
            else:
                results[metric] = False

        return results

    def print_console_output(self, kpis: Dict[str, float], validations: Dict[str, bool]):
        """Print KPI data to console."""
        print("\n" + "="*50)
        print("🤖 AI DIALER KPI SYNTHETIC DATA")
        print("="*50)
        print(f"Generated: {kpis['generated_at']}")
        print(f"Data Quality: {kpis['data_quality']}")
        print()

        for metric, value in kpis.items():
            if metric == "generated_at" or metric == "data_quality":
                continue

            target = KPI_TARGETS.get(metric, "N/A")
            status = "✅ PASS" if validations.get(metric, False) else "❌ FAIL"

            print(f"{metric:<25} | {value:>8.2f} | {target:>8} | {status}")
            print(f"{'-' * 25} | {'-' * 8} | {'-' * 8} | {'-' * 8}")

        print("\n" + "="*50)

        # Overall status
        all_passed = all(validations.values())
        overall_status = "🎉 ALL KPIs PASS" if all_passed else "⚠️  SOME KPIs FAIL"
        print(f"Overall: {overall_status}")
        print("="*50)

    def save_to_file(self, kpis: Dict[str, float]):
        """Save KPI data to artifacts/kpis.json."""
        ARTIFACTS_DIR.mkdir(exist_ok=True)

        kpi_file = ARTIFACTS_DIR / "kpis.json"

        # Add metadata
        kpis["version"] = "1.0"
        kpis["source"] = "synthetic_generator"
        kpis["environment"] = os.getenv("ENVIRONMENT", "development")

        with open(kpi_file, 'w') as f:
            json.dump(kpis, f, indent=2)

        logger.info(f"📁 KPIs saved to {kpi_file}")

    def run(self):
        """Main execution."""
        logger.info("🚀 Generating synthetic KPI data...")

        # Generate data
        kpis = self.generate_synthetic_data()

        # Validate against targets
        validations = self.validate_kpis(kpis)

        # Print to console
        self.print_console_output(kpis, validations)

        # Save to file
        self.save_to_file(kpis)

        # Return success based on KPI validation
        success = all(validations.values())

        logger.info(f"✅ KPI generation {'PASSED' if success else 'FAILED'}")

        return success


def main():
    """Main entry point."""
    try:
        generator = KPISyntheticGenerator()
        success = generator.run()

        if not success:
            logger.warning("⚠️ Some KPIs did not meet targets")
            sys.exit(1)
        else:
            logger.info("🎉 All KPIs meet targets!")
            sys.exit(0)

    except Exception as e:
        logger.error(f"❌ KPI generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
