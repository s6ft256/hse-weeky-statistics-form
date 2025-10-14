"""
Tests for the modernized AirtableClient.

Run with: pytest tests/test_client.py -v
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from pyairtable import AirtableClient
from pyairtable.api import Api


class TestAirtableClient:
    """Tests for AirtableClient initialization and configuration."""
    
    def test_init_with_explicit_credentials(self):
        """Test initialization with explicit token and base_id."""
        client = AirtableClient(token="patTEST123", base_id="appTEST123")
        
        assert client.token == "patTEST123"
        assert client.base_id == "appTEST123"
        assert isinstance(client._api, Api)
    
    def test_init_with_environment_variables(self):
        """Test initialization using environment variables."""
        with patch.dict(os.environ, {
            "AIRTABLE_TOKEN": "patENV123",
            "AIRTABLE_BASE_ID": "appENV123"
        }):
            client = AirtableClient()
            
            assert client.token == "patENV123"
            assert client.base_id == "appENV123"
    
    def test_init_missing_token(self):
        """Test that ValueError is raised when token is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="token is required"):
                AirtableClient(base_id="appTEST123")
    
    def test_init_missing_base_id(self):
        """Test that ValueError is raised when base_id is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="base_id is required"):
                AirtableClient(token="patTEST123")
    
    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        client = AirtableClient(
            token="patTEST123",
            base_id="appTEST123",
            timeout=(5, 30)
        )
        
        assert client._api.timeout == (5, 30)
    
    def test_init_with_retries_disabled(self):
        """Test initialization with retries disabled."""
        client = AirtableClient(
            token="patTEST123",
            base_id="appTEST123",
            enable_retries=False
        )
        
        # The API should be initialized
        assert isinstance(client._api, Api)
    
    def test_init_with_verify_ssl_param(self):
        """Test that verify_ssl parameter disables TLS verification."""
        client = AirtableClient(
            token="patTEST123",
            base_id="appTEST123",
            verify_ssl=False,
        )

        assert client._api.session.verify is False

    def test_init_with_verify_ssl_env(self):
        """Test that AIRTABLE_VERIFY_SSL env flag is respected."""
        with patch.dict(os.environ, {
            "AIRTABLE_TOKEN": "patENV123",
            "AIRTABLE_BASE_ID": "appENV123",
            "AIRTABLE_VERIFY_SSL": "false",
        }, clear=True):
            client = AirtableClient()

        assert client._api.session.verify is False

    def test_init_with_custom_ca_bundle(self, tmp_path):
        """Test that a custom CA bundle can be configured via env."""
        bundle = tmp_path / "corp-ca.pem"
        bundle.write_text("dummy cert")

        with patch.dict(os.environ, {
            "AIRTABLE_TOKEN": "patENV123",
            "AIRTABLE_BASE_ID": "appENV123",
            "AIRTABLE_CA_BUNDLE": str(bundle),
        }, clear=True):
            client = AirtableClient()

        assert client._api.session.verify == str(bundle)

    def test_repr(self):
        """Test string representation of client."""
        client = AirtableClient(token="patTEST123", base_id="appTEST123")
        
        repr_str = repr(client)
        assert "AirtableClient" in repr_str
        assert "appTEST1" in repr_str  # First 8 chars


class TestAirtableClientMethods:
    """Tests for AirtableClient CRUD methods."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return AirtableClient(token="patTEST123", base_id="appTEST123")
    
    @pytest.fixture
    def mock_table(self, client):
        """Create a mocked table."""
        mock = MagicMock()
        client._tables["TestTable"] = mock
        return mock
    
    def test_get_records_basic(self, client, mock_table):
        """Test basic get_records call."""
        mock_table.all.return_value = [
            {"id": "rec1", "fields": {"Name": "Alice"}},
            {"id": "rec2", "fields": {"Name": "Bob"}},
        ]
        
        records = client.get_records("TestTable")
        
        assert len(records) == 2
        assert records[0]["fields"]["Name"] == "Alice"
        mock_table.all.assert_called_once()
    
    def test_get_records_with_filters(self, client, mock_table):
        """Test get_records with filters."""
        mock_table.all.return_value = []
        
        client.get_records(
            "TestTable",
            filters="{Status} = 'Active'",
            fields=["Name", "Email"],
            sort=[("Name", "asc")],
            max_records=10
        )
        
        call_kwargs = mock_table.all.call_args[1]
        assert call_kwargs["formula"] == "{Status} = 'Active'"
        assert call_kwargs["fields"] == ["Name", "Email"]
        assert call_kwargs["sort"] == ["Name:asc"]
        assert call_kwargs["max_records"] == 10
    
    def test_create_record(self, client, mock_table):
        """Test create_record."""
        mock_table.create.return_value = {
            "id": "recNEW",
            "fields": {"Name": "Charlie"},
            "createdTime": "2025-10-14T12:00:00.000Z"
        }
        
        record = client.create_record("TestTable", {"Name": "Charlie"})
        
        assert record["id"] == "recNEW"
        assert record["fields"]["Name"] == "Charlie"
        mock_table.create.assert_called_once_with(
            fields={"Name": "Charlie"},
            typecast=False
        )
    
    def test_update_record(self, client, mock_table):
        """Test update_record."""
        mock_table.update.return_value = {
            "id": "rec1",
            "fields": {"Name": "Alice", "Status": "Active"},
            "createdTime": "2025-10-14T12:00:00.000Z"
        }
        
        record = client.update_record(
            "TestTable",
            "rec1",
            {"Status": "Active"}
        )
        
        assert record["fields"]["Status"] == "Active"
        mock_table.update.assert_called_once_with(
            record_id="rec1",
            fields={"Status": "Active"},
            replace=False,
            typecast=False
        )
    
    def test_update_record_with_replace(self, client, mock_table):
        """Test update_record with replace=True."""
        mock_table.update.return_value = {
            "id": "rec1",
            "fields": {"Name": "Alice"},
        }
        
        client.update_record(
            "TestTable",
            "rec1",
            {"Name": "Alice"},
            replace=True
        )
        
        mock_table.update.assert_called_once()
        assert mock_table.update.call_args[1]["replace"] is True
    
    def test_delete_record(self, client, mock_table):
        """Test delete_record."""
        mock_table.delete.return_value = {
            "id": "rec1",
            "deleted": True
        }
        
        result = client.delete_record("TestTable", "rec1")
        
        assert result["deleted"] is True
        assert result["id"] == "rec1"
        mock_table.delete.assert_called_once_with(record_id="rec1")
    
    def test_get_record(self, client, mock_table):
        """Test get_record."""
        mock_table.get.return_value = {
            "id": "rec1",
            "fields": {"Name": "Alice"},
            "createdTime": "2025-10-14T12:00:00.000Z"
        }
        
        record = client.get_record("TestTable", "rec1")
        
        assert record["id"] == "rec1"
        assert record["fields"]["Name"] == "Alice"
        mock_table.get.assert_called_once_with(record_id="rec1")
    
    def test_batch_create(self, client, mock_table):
        """Test batch_create."""
        mock_table.batch_create.return_value = [
            {"id": "rec1", "fields": {"Name": "Alice"}},
            {"id": "rec2", "fields": {"Name": "Bob"}},
        ]
        
        records = client.batch_create("TestTable", [
            {"Name": "Alice"},
            {"Name": "Bob"}
        ])
        
        assert len(records) == 2
        mock_table.batch_create.assert_called_once()
    
    def test_batch_update(self, client, mock_table):
        """Test batch_update."""
        mock_table.batch_update.return_value = [
            {"id": "rec1", "fields": {"Status": "Active"}},
            {"id": "rec2", "fields": {"Status": "Inactive"}},
        ]
        
        updates = [
            {"id": "rec1", "fields": {"Status": "Active"}},
            {"id": "rec2", "fields": {"Status": "Inactive"}},
        ]
        
        records = client.batch_update("TestTable", updates)
        
        assert len(records) == 2
        mock_table.batch_update.assert_called_once()
    
    def test_batch_delete(self, client, mock_table):
        """Test batch_delete."""
        mock_table.batch_delete.return_value = [
            {"id": "rec1", "deleted": True},
            {"id": "rec2", "deleted": True},
        ]
        
        results = client.batch_delete("TestTable", ["rec1", "rec2"])
        
        assert len(results) == 2
        assert all(r["deleted"] for r in results)
        mock_table.batch_delete.assert_called_once_with(record_ids=["rec1", "rec2"])
    
    def test_table_caching(self, client):
        """Test that table instances are cached."""
        # Access the same table twice
        table1 = client._get_table("TestTable")
        table2 = client._get_table("TestTable")
        
        # Should be the same instance
        assert table1 is table2
        
        # Should be in cache
        assert "TestTable" in client._tables
