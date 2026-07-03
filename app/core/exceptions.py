"""
Custom business exceptions used across the application
These exceptions keep domain logic independent from FastAPI and HTTP concerns
"""

__all__ = [
    "BaseBusinessException",
    # Base categorized exceptions
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    "AuthenticationError",
    # Concrete exceptions
    "UserNotFoundError",
    "EmailAlreadyExistsError",
    "InvalidCredentialsError",
    "PatientNotFoundError",
    "DocumentNumberAlreadyExistsError",
    "AppointmentNotFoundError",
    "DoubleBookingError",
    "InvalidAppointmentStateTransitionError",
    "PastAppointmentError",
    "InvalidDoctorProfileError",
    "InvalidCatalogReferenceError",
    "DoctorNotAvailableError",
]

class BaseBusinessException(Exception):
    """
    Root exception for all domain logic failures
    Allows global exception handlers to catch and map these to standard HTTP responses
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class NotFoundError(BaseBusinessException):
    """Raised when a requested resource does not exist (e.g., user not found, appointment not found)"""


class ConflictError(BaseBusinessException):
    """Raised when a resource conflicts with existing data (e.g., duplicate email, double booking)"""


class ValidationError(BaseBusinessException):
    """Raised when business validation rules fail (e.g., invalid state transitions, missing required fields)"""


class AuthenticationError(BaseBusinessException):
    """Raised when authentication fails (e.g., invalid credentials)"""


# STAFF & AUTH EXCEPTIONS
class UserNotFoundError(NotFoundError):
    def __init__(self, identifier: str):
        super().__init__(f"Staff member with identifier '{identifier}' not found")


class EmailAlreadyExistsError(ConflictError):
    def __init__(self, email: str):
        super().__init__(f"The email '{email}' is already registered in the system")


class InvalidCredentialsError(AuthenticationError):
    def __init__(self):
        super().__init__("Invalid email or password")


class InvalidDoctorProfileError(ValidationError):
    def __init__(self, detail: str):
        super().__init__(detail)


# PATIENTS EXCEPTIONS
class PatientNotFoundError(NotFoundError):
    def __init__(self, identifier: str):
        super().__init__(f"Patient with identifier '{identifier}' not found")


class DocumentNumberAlreadyExistsError(ConflictError):
    def __init__(self, document: str):
        super().__init__(f"The document number '{document}' is already registered")


class InvalidCatalogReferenceError(ValidationError):
    def __init__(self, catalog_name: str):
        super().__init__(f"One or more provided IDs for {catalog_name} do not exist in the database")


# APPOINTMENTS EXCEPTIONS
class AppointmentNotFoundError(NotFoundError):
    def __init__(self, identifier: str):
        super().__init__(f"Appointment with identifier '{identifier}' not found")


class DoubleBookingError(ConflictError):
    def __init__(self):
        super().__init__("The requested time slot is already booked for this doctor")


class PastAppointmentError(ValidationError):
    def __init__(self):
        super().__init__("Cannot schedule an appointment in the past")


class InvalidAppointmentStateTransitionError(ValidationError):
    def __init__(self, current_status: str, target_status: str):
        super().__init__(f"Cannot transition appointment from {current_status} to {target_status}")

class DoctorNotAvailableError(ValidationError):
    def __init__(self, doctor_id: str, day_of_week: int):
        super().__init__(f"The doctor is not available on day of week {day_of_week} or within the requested time range")
