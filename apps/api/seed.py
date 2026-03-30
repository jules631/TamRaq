#!/usr/bin/env python3
"""
Seed script: create a tenant and add a user as a member.

Usage:
    AUTH0_USER_ID=auth0|xxx python seed.py [--tenant-name "My Org"] [--slug my-org]

Environment variables read from .env automatically via pydantic-settings.
DATABASE_URL must be set (or default to localhost).
"""

import argparse
import os
import sys
import uuid

# Allow running from the apps/api directory
sys.path.insert(0, os.path.dirname(__file__))

from app.db.models import Tenant, TenantMember  # noqa: E402
from app.db.session import engine, SessionLocal  # noqa: E402
from app.db.base import Base  # noqa: E402


def seed(tenant_name: str, slug: str, auth0_user_id: str) -> None:
    with SessionLocal() as db:
        # Check if tenant with slug already exists
        existing = db.query(Tenant).filter(Tenant.slug == slug).first()
        if existing:
            tenant = existing
            print(f"Tenant '{slug}' already exists (id={tenant.id})")
        else:
            tenant = Tenant(id=uuid.uuid4(), name=tenant_name, slug=slug)
            db.add(tenant)
            db.flush()
            print(f"Created tenant '{tenant_name}' (id={tenant.id})")

        # Check member
        existing_member = (
            db.query(TenantMember)
            .filter(
                TenantMember.tenant_id == tenant.id,
                TenantMember.auth0_user_id == auth0_user_id,
            )
            .first()
        )
        if existing_member:
            print(f"User '{auth0_user_id}' is already a member")
        else:
            member = TenantMember(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                auth0_user_id=auth0_user_id,
            )
            db.add(member)
            print(f"Added '{auth0_user_id}' as member of tenant {tenant.id}")

        db.commit()
        print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed tenant and member")
    parser.add_argument("--tenant-name", default="Demo Organization")
    parser.add_argument("--slug", default="demo")
    parser.add_argument(
        "--auth0-user-id",
        default=os.environ.get("AUTH0_USER_ID", ""),
        help="Auth0 user ID (sub claim), e.g. auth0|abc123",
    )
    args = parser.parse_args()

    if not args.auth0_user_id:
        print("ERROR: Provide --auth0-user-id or set AUTH0_USER_ID env var")
        sys.exit(1)

    seed(args.tenant_name, args.slug, args.auth0_user_id)
