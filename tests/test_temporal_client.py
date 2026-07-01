"""Tests for Temporal client — F-03.

Verifies workflow definitions and client logic with mocked Temporal.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.temporal_client import (
    TemporalClient,
    compensate_payment,
    initiate_payment,
    select_payment_method,
    validate_subsidy_eligibility,
)

# ─── Activity Tests ──────────────────────────────────────────────────────────


class TestTemporalActivities:
    """Test Temporal activity functions."""

    @pytest.mark.asyncio
    async def test_validate_subsidy_eligibility(self):
        """Should validate eligibility."""
        result = await validate_subsidy_eligibility(
            {"subsidy_id": "sub-test", "amount": 50000}
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_select_payment_method_stablecoin(self):
        """Should select STABLECOIN for amounts >= $500k."""
        result = await select_payment_method(
            {"subsidy_amount_cents": 50_000_000}
        )
        assert result["payment_method"] == "STABLECOIN"

    @pytest.mark.asyncio
    async def test_select_payment_method_wire(self):
        """Should select WIRE for amounts >= $100k."""
        result = await select_payment_method(
            {"subsidy_amount_cents": 10_000_000}
        )
        assert result["payment_method"] == "WIRE"

    @pytest.mark.asyncio
    async def test_select_payment_method_ach(self):
        """Should select ACH for amounts < $100k."""
        result = await select_payment_method(
            {"subsidy_amount_cents": 5_000_000}
        )
        assert result["payment_method"] == "ACH"

    @pytest.mark.asyncio
    async def test_initiate_payment(self):
        """Should initiate payment and return reference."""
        result = await initiate_payment(
            {"subsidy_id": "sub-test", "amount": 50000},
            "ACH",
        )
        assert "payment_reference" in result
        assert result["payment_reference"].startswith("pay-")

    @pytest.mark.asyncio
    async def test_compensate_payment(self):
        """Should compensate a failed payment."""
        result = await compensate_payment({"subsidy_id": "sub-test"})
        assert result["compensated"] is True


# ─── Client Tests ────────────────────────────────────────────────────────────


class TestTemporalClient:
    """Test Temporal client operations."""

    @pytest.mark.asyncio
    async def test_connect(self):
        """Should connect to Temporal server."""
        client = TemporalClient()
        mock_client = AsyncMock()
        mock_client.close = AsyncMock()

        with patch(
            "src.services.temporal_client.Client"
        ) as mock_client_cls:
            mock_client_cls.connect = AsyncMock(return_value=mock_client)

            connected = await client.connect()
            assert connected is mock_client

    @pytest.mark.asyncio
    async def test_start_subsidy_workflow(self):
        """Should start a workflow."""
        client = TemporalClient()
        mock_client = AsyncMock()
        mock_handle = MagicMock()
        mock_client.start_workflow = AsyncMock(return_value=mock_handle)

        with patch(
            "src.services.temporal_client.Client"
        ) as mock_client_cls:
            mock_client_cls.connect = AsyncMock(return_value=mock_client)
            client._client = mock_client

            workflow_id = await client.start_subsidy_workflow(
                {"subsidy_id": "sub-001", "amount": 50000}
            )
            assert "sub-001" in workflow_id
            mock_client.start_workflow.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_workflow(self):
        """Should cancel a workflow."""
        client = TemporalClient()
        mock_client = AsyncMock()
        mock_handle = MagicMock()
        mock_handle.cancel = AsyncMock()
        mock_client.get_workflow_handle = MagicMock(return_value=mock_handle)

        client._client = mock_client
        await client.cancel_workflow("subsidy-sub-001")
        mock_handle.cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Should disconnect from Temporal."""
        client = TemporalClient()
        mock_client = AsyncMock()
        mock_client.close = AsyncMock()
        client._client = mock_client

        await client.disconnect()
        assert client._client is None
        mock_client.close.assert_called_once()
