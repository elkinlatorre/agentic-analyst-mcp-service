import re

class SQLSecurityValidator:
    """Validates SQL queries to prevent unauthorized DDL operations."""

    FORBIDDEN_COMMANDS = [
        r"\bCREATE\b",
        r"\bDROP\b",
        r"\bALTER\b",
        r"\bTRUNCATE\b",
        r"\bRENAME\b",
        r"\bDELETE\b"
    ]

    @staticmethod
    def validate_query(query: str) -> bool:
        """Returns True if the query is safe (DML only), False otherwise."""
        query_upper = query.upper()
        for command in SQLSecurityValidator.FORBIDDEN_COMMANDS:
            if re.search(command, query_upper):
                return False
        return True

    @staticmethod
    def get_security_error_message() -> str:
        return (
            "ERROR: Security Policy Violation. You are only allowed to perform "
            "DML operations (SELECT, INSERT, UPDATE) on existing tables. "
            "Schema modifications (CREATE, DROP, etc.) are strictly prohibited."
            "DO NOT retry this action. Move to the next task or inform the user that this "
            "action is not allowed by corporate policy."
        )