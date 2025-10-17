"""
Modern Airtable API Client with simplified interface.

This module provides a streamlined client for interacting with Airtable's API
using Personal Access Tokens (PAT) for authentication.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pyairtable.api import Api, Table
from pyairtable.api.types import (RecordDict, WritableFields, UpdateRecordDict, RecordDeletedDict)
from pyairtable.formulas import Formula


logger = logging.getLogger(__name__)


class AirtableClient:
    """
    Modern Airtable API client with simplified CRUD operations.
    
    This client provides a clean, intuitive interface for interacting with
    Airtable bases using Personal Access Token (PAT) authentication.
    
    Features:
        - PAT-based authentication
        - Automatic pagination handling
        - Built-in rate limiting with retry logic
        - Graceful error handling
        - Clean, well-typed method signatures
    
    Usage:
        >>> from pyairtable import AirtableClient
        >>> client = AirtableClient(token="your_token", base_id="appXXX")
        >>> records = client.get_records("TableName")
        >>> new_record = client.create_record("TableName", {"Name": "Alice"})
        >>> updated = client.update_record("TableName", "recXXX", {"Name": "Bob"})
        >>> client.delete_record("TableName", "recXXX")
    
    Environment Variables:
        The client can automatically read credentials from:
        - AIRTABLE_TOKEN: Your Personal Access Token
        - AIRTABLE_BASE_ID: Your base ID
    """
    # Narrow instance attribute types so the type-checker knows these are strings after init
    token: str
    base_id: str

    def __init__(
        self,
        token: Optional[str] = None,
        base_id: Optional[str] = None,
    *,
    timeout: Optional[tuple[int, int]] = None,
    enable_retries: bool = True,
    endpoint_url: str = "https://api.airtable.com",
    verify_ssl: Optional[bool] = None,
    ca_bundle: Optional[str] = None,
    ) -> None:
        """
        Initialize the Airtable client.
        
        Args:
            token: Airtable Personal Access Token. If not provided, will read from
                AIRTABLE_TOKEN environment variable.
            base_id: Airtable base ID (starts with 'app'). If not provided, will read
                from AIRTABLE_BASE_ID environment variable.
            timeout: Optional tuple of (connect_timeout, read_timeout) in seconds.
                Example: (5, 30) for 5s connect, 30s read timeout.
            enable_retries: Enable automatic retry logic for rate limits (HTTP 429)
                and transient errors. Default: True.
            endpoint_url: The Airtable API endpoint. Override for testing/proxying.
            verify_ssl: Override SSL verification behaviour. ``True`` enforces default
                certificate checks, ``False`` disables verification (development only),
                and ``None`` defers to environment configuration.
            ca_bundle: Optional path to a custom CA bundle file. If provided (or set via
                ``AIRTABLE_CA_BUNDLE``), requests will trust the certificates in that file.
        
        Raises:
            ValueError: If token or base_id is not provided and not in environment.
        
        Example:
            >>> # Using explicit parameters
            >>> client = AirtableClient(token="patXXX", base_id="appXXX")
            
            >>> # Using environment variables
            >>> import os
            >>> os.environ["AIRTABLE_TOKEN"] = "patXXX"
            >>> os.environ["AIRTABLE_BASE_ID"] = "appXXX"
            >>> client = AirtableClient()
        """
        # Read from environment variables if not provided
        self.token = token or os.getenv("AIRTABLE_TOKEN")
        self.base_id = base_id or os.getenv("AIRTABLE_BASE_ID")
        
        # Validate required credentials
        if not self.token:
            raise ValueError(
                "Airtable token is required. Provide 'token' parameter or set "
                "AIRTABLE_TOKEN environment variable."
            )
        if not self.base_id:
            raise ValueError(
                "Airtable base_id is required. Provide 'base_id' parameter or set "
                "AIRTABLE_BASE_ID environment variable."
            )

        # Tell the type-checker these are non-None strings from here on
        assert self.token is not None
        assert self.base_id is not None

        # Initialize the underlying API client
        self._api = Api(
            api_key=self.token,
            timeout=timeout,
            retry_strategy=enable_retries,
            endpoint_url=endpoint_url,
        )

        # Configure SSL verification behaviour
        env_verify = os.getenv("AIRTABLE_VERIFY_SSL") if verify_ssl is None else None
        if env_verify is not None:
            env_verify_clean = env_verify.strip().lower()
            if env_verify_clean in {"0", "false", "no", "off"}:
                verify_ssl = False
            elif env_verify_clean in {"1", "true", "yes", "on"}:
                verify_ssl = True

        resolved_ca_bundle = ca_bundle or os.getenv("AIRTABLE_CA_BUNDLE")
        bundle_path: Optional[Path] = None
        if resolved_ca_bundle:
            bundle_path = Path(resolved_ca_bundle).expanduser()
            if bundle_path.exists():
                self._api.session.verify = str(bundle_path)
                logger.info(
                    "Configured AirtableClient with custom CA bundle at %s",
                    bundle_path,
                )
            else:
                logger.warning(
                    "AIRTABLE_CA_BUNDLE path does not exist: %s",
                    bundle_path,
                )
                bundle_path = None

        if verify_ssl is False:
            self._api.session.verify = False
            logger.warning(
                "SSL verification disabled for AirtableClient session. "
                "Use only in trusted development environments."
            )
            suppress_warnings = os.getenv("AIRTABLE_SUPPRESS_SSL_WARNINGS", "").strip().lower()
            if suppress_warnings in {"1", "true", "yes", "on"}:
                try:
                    import urllib3

                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                    logger.info("Suppressed urllib3 InsecureRequestWarning as requested.")
                except Exception as exc:  # pragma: no cover - defensive logging
                    logger.debug("Could not suppress SSL warnings: %s", exc)
        elif verify_ssl is True and bundle_path is None:
            # Explicit re-enable when previously disabled via environment.
            self._api.session.verify = True
            logger.info("SSL verification explicitly enabled for AirtableClient session.")

        self.verify_ssl = self._api.session.verify
        self.ca_bundle = str(bundle_path) if bundle_path else None
        
        # Cache for table instances
        self._tables: Dict[str, Table] = {}
        
        logger.info(
            f"Initialized AirtableClient for base {self.base_id[:8]}... "
            f"(retries: {enable_retries})"
        )
    
    def _get_table(self, table_name: str) -> Table:
        """
        Get or create a cached Table instance.
        
        Args:
            table_name: Name or ID of the table.
        
        Returns:
            Table instance for the specified table.
        """
        if table_name not in self._tables:
            self._tables[table_name] = self._api.table(self.base_id, table_name)
            logger.debug(f"Created table instance for: {table_name}")
        return self._tables[table_name]
    
    def get_records(
        self,
        table_name: str,
        filters: Optional[Union[str, Formula]] = None,
        fields: Optional[List[str]] = None,
        sort: Optional[List[tuple[str, str]]] = None,
        max_records: Optional[int] = None,
        view: Optional[str] = None,
    ) -> List[RecordDict]:
        """
        Retrieve records from a table with optional filtering and sorting.
        
        This method automatically handles pagination and returns all matching records.
        """
        table = self._get_table(table_name)
        
        options: Dict[str, Any] = {}
        if filters:
            options["formula"] = filters
        if fields:
            options["fields"] = fields
        if sort:
            options["sort"] = [f"{field}:{direction}" for field, direction in sort]
        if max_records:
            options["max_records"] = max_records
        if view:
            options["view"] = view
        
        logger.info(f"Fetching records from {table_name} with options: {options}")
        records = table.all(**options)
        logger.info(f"Retrieved {len(records)} records from {table_name}")
        
        return records
    
    def create_record(
        self,
        table_name: str,
        data: WritableFields,
        typecast: bool = False,
    ) -> RecordDict:
        table = self._get_table(table_name)
        
        logger.info(f"Creating record in {table_name}: {data}")
        record = table.create(fields=data, typecast=typecast)
        logger.info(f"Created record {record['id']} in {table_name}")
        
        return record
    
    def update_record(
        self,
        table_name: str,
        record_id: str,
        data: WritableFields,
        replace: bool = False,
        typecast: bool = False,
    ) -> RecordDict:
        table = self._get_table(table_name)
        
        logger.info(
            f"Updating record {record_id} in {table_name} "
            f"(replace={replace}): {data}"
        )
        record = table.update(
            record_id=record_id,
            fields=data,
            replace=replace,
            typecast=typecast,
        )
        logger.info(f"Updated record {record_id} in {table_name}")
        
        return record
    
    def delete_record(
        self,
        table_name: str,
        record_id: str,
    ) -> RecordDeletedDict:
        table = self._get_table(table_name)
        
        logger.info(f"Deleting record {record_id} from {table_name}")
        result = table.delete(record_id=record_id)
        logger.info(f"Deleted record {record_id} from {table_name}")
        
        return result
    
    def batch_create(
        self,
        table_name: str,
        records: List[WritableFields],
        typecast: bool = False,
    ) -> List[RecordDict]:
        table = self._get_table(table_name)
        
        logger.info(f"Batch creating {len(records)} records in {table_name}")
        created_records = table.batch_create(records=records, typecast=typecast)
        logger.info(f"Created {len(created_records)} records in {table_name}")
        
        return created_records
    
    def batch_update(
        self,
        table_name: str,
        updates: List[UpdateRecordDict],
        replace: bool = False,
        typecast: bool = False,
    ) -> List[RecordDict]:
        table = self._get_table(table_name)
        
        logger.info(f"Batch updating {len(updates)} records in {table_name}")
        updated_records = table.batch_update(
            records=updates,
            replace=replace,
            typecast=typecast,
        )
        logger.info(f"Updated {len(updated_records)} records in {table_name}")
        
        return updated_records
    
    def batch_delete(
        self,
        table_name: str,
        record_ids: List[str],
    ) -> List[RecordDeletedDict]:
        table = self._get_table(table_name)
        
        logger.info(f"Batch deleting {len(record_ids)} records from {table_name}")
        deleted_records = table.batch_delete(record_ids=record_ids)
        logger.info(f"Deleted {len(deleted_records)} records from {table_name}")
        
        return deleted_records
    
    def get_record(
        self,
        table_name: str,
        record_id: str,
    ) -> RecordDict:
        table = self._get_table(table_name)
        
        logger.info(f"Fetching record {record_id} from {table_name}")
        record = table.get(record_id=record_id)
        logger.info(f"Retrieved record {record_id} from {table_name}")
        
        return record
    
    def __repr__(self) -> str:
        """String representation of the client."""
        base = self.base_id or ""
        base_preview = f"{base[:8]}..." if len(base) > 8 else base
        return f"<AirtableClient base={base_preview}>"


__all__ = ["AirtableClient"]
