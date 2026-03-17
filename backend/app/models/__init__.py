"""
Database models (tables) for the import pipeline and analytics.

ImportBatch -> RawMeterReading -> NormalizedMeterReading -> DailyMeterConsumption.
We also have DailyEnergySharing (PV allocation) and DataQualityIssue (quality findings).
"""
from app.models.import_batch import ImportBatch
from app.models.raw_meter_reading import RawMeterReading
from app.models.normalized_meter_reading import NormalizedMeterReading
from app.models.daily_meter_consumption import DailyMeterConsumption
from app.models.daily_energy_sharing import DailyEnergySharing
from app.models.data_quality_issue import DataQualityIssue

__all__ = [
    "ImportBatch",
    "RawMeterReading",
    "NormalizedMeterReading",
    "DailyMeterConsumption",
    "DailyEnergySharing",
    "DataQualityIssue",
]
