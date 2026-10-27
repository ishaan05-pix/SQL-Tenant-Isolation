"""Pure identity/pool binding checks used before any DB connection is queried.

This module validates a configuration mapping. It is not a DB driver and does
not prove PostgreSQL pool behavior.
"""

from __future__ import annotations


class IdentityBindingError(ValueError):
    pass


class TenantPoolBindings:
    def __init__(self, principal_by_tenant: dict[str, str]):
        if not principal_by_tenant or len(set(principal_by_tenant.values())) != len(principal_by_tenant):
            raise IdentityBindingError("tenant_principals_must_be_unique")
        self._principal_by_tenant = dict(principal_by_tenant)

    def validate(self, request_tenant: str, actual_principal: str) -> None:
        expected = self._principal_by_tenant.get(request_tenant)
        if expected is None:
            raise IdentityBindingError("unknown_request_tenant")
        if actual_principal != expected:
            raise IdentityBindingError("request_database_principal_mismatch")

    def pool_key(self, request_tenant: str) -> str:
        principal = self._principal_by_tenant.get(request_tenant)
        if principal is None:
            raise IdentityBindingError("unknown_request_tenant")
        return principal

    def assert_checkout(self, request_tenant: str, connection_principal: str) -> None:
        self.validate(request_tenant, connection_principal)
