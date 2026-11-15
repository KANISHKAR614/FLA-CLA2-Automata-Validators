"""Task 2: finite automata for real-time validation (mobile number, vehicle registration, date of birth)."""

from .mobile import build_mobile_dfa
from .vehicle import build_vehicle_dfa, build_vehicle_nfa
from .dob import build_dob_dfa

ALL = {
    "mobile": build_mobile_dfa,
    "vehicle": build_vehicle_dfa,
    "dob": build_dob_dfa,
}

__all__ = ["build_mobile_dfa", "build_vehicle_dfa", "build_vehicle_nfa", "build_dob_dfa", "ALL"]
