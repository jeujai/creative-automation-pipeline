"""Unit tests for PipelineReporter."""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from src.utils.reporter import PipelineReporter
from src.models import PipelineResult, GeneratedAsset, ComplianceResult


class TestPipelineReporter:
    """Test suite for PipelineReporter class."""

    @pytest.fixture
    def sample_assets(self):
        """Fixture providing sample generated assets."""
        return [
            GeneratedAsset(
                product_id="product_a",
                aspect_ratio="1:1",
                file_path="output/campaign_001/product_a/1x1_product_a.png",
                was_generated=True
            ),
            GeneratedAsset(
                product_id="product_a",
                aspect_ratio="9:16",
                file_path="output/campaign_001/product_a/9x16_product_a.png",
                was_generated=True
            ),
            GeneratedAsset(
                product_id="product_b",
                aspect_ratio="1:1",
                file_path="output/campaign_001/product_b/1x1_product_b.png",
                was_generated=False
            )
        ]

    @pytest.fixture
    def sample_result(self, sample_assets):
        """Fixture providing sample pipeline result."""
        return PipelineResult(
            campaign_id="campaign_001",
            outputs=sample_assets,
            execution_time=45.5,
            success=True,
            errors=[]
        )

    @pytest.fixture
    def failed_result(self):
        """Fixture providing a failed pipeline result."""
        return PipelineResult(
            campaign_id="campaign_002",
            outputs=[],
            execution_time=10.2,
            success=False,
            errors=["GenAI API error", "Network timeout"]
        )

    def test_generate_report_basic(self, sample_result):
        """Test generating a basic report."""
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime(2024, 1, 1, 10, 0, 45)
        
        report = PipelineReporter.generate_report(
            sample_result,
            start_time,
            end_time
        )
        
        assert report["campaign_id"] == "campaign_001"
        assert report["success"] is True
        assert report["execution_time_seconds"] == 45.5
        assert report["summary"]["products_processed"] == 2
        assert report["summary"]["total_assets"] == 3
        assert report["summary"]["assets_generated"] == 2
        assert report["summary"]["assets_reused"] == 1

    def test_generate_report_product_ids(self, sample_result):
        """Test report includes correct product IDs."""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=45)
        
        report = PipelineReporter.generate_report(
            sample_result,
            start_time,
            end_time
        )
        
        product_ids = report["summary"]["product_ids"]
        assert len(product_ids) == 2
        assert "product_a" in product_ids
        assert "product_b" in product_ids

    def test_generate_report_outputs(self, sample_result):
        """Test report includes output details."""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=45)
        
        report = PipelineReporter.generate_report(
            sample_result,
            start_time,
            end_time
        )
        
        assert len(report["outputs"]) == 3
        
        output_1 = report["outputs"][0]
        assert output_1["product_id"] == "product_a"
        assert output_1["aspect_ratio"] == "1:1"
        assert output_1["file_path"] == "output/campaign_001/product_a/1x1_product_a.png"
        assert output_1["was_generated"] is True

    def test_generate_report_with_errors(self, failed_result):
        """Test report includes error information."""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=10)
        
        report = PipelineReporter.generate_report(
            failed_result,
            start_time,
            end_time
        )
        
        assert report["success"] is False
        assert len(report["errors"]) == 2
        assert "GenAI API error" in report["errors"]
        assert "Network timeout" in report["errors"]

    def test_generate_report_with_compliance(self, sample_assets):
        """Test report includes compliance results."""
        # Add compliance status to assets
        sample_assets[0].compliance_status = ComplianceResult(
            passed=True,
            details="All checks passed",
            violations=[]
        )
        sample_assets[1].compliance_status = ComplianceResult(
            passed=False,
            details="Logo not detected",
            violations=["Missing brand logo"]
        )
        
        result = PipelineResult(
            campaign_id="campaign_001",
            outputs=sample_assets,
            execution_time=45.5,
            success=True,
            errors=[]
        )
        
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=45)
        
        report = PipelineReporter.generate_report(
            result,
            start_time,
            end_time
        )
        
        assert report["compliance_results"] is not None
        assert len(report["compliance_results"]) == 2
        
        comp_1 = report["compliance_results"][0]
        assert comp_1["product_id"] == "product_a"
        assert comp_1["passed"] is True
        assert comp_1["violations"] == []
        
        comp_2 = report["compliance_results"][1]
        assert comp_2["product_id"] == "product_a"
        assert comp_2["passed"] is False
        assert "Missing brand logo" in comp_2["violations"]

    def test_generate_report_saves_to_file(self, sample_result):
        """Test report is saved to file when path provided."""
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.json"
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=45)
            
            report = PipelineReporter.generate_report(
                sample_result,
                start_time,
                end_time,
                output_path=str(output_path)
            )
            
            assert output_path.exists()
            
            # Verify file content
            with open(output_path, 'r') as f:
                saved_report = json.load(f)
            
            assert saved_report["campaign_id"] == report["campaign_id"]
            assert saved_report["success"] == report["success"]

    def test_generate_report_creates_output_directory(self, sample_result):
        """Test report creation creates output directory if needed."""
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "reports" / "subdir" / "report.json"
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=45)
            
            PipelineReporter.generate_report(
                sample_result,
                start_time,
                end_time,
                output_path=str(output_path)
            )
            
            assert output_path.exists()
            assert output_path.parent.exists()

    def test_format_summary_basic(self, sample_result):
        """Test formatting report as human-readable summary."""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=45)
        
        report = PipelineReporter.generate_report(
            sample_result,
            start_time,
            end_time
        )
        
        summary = PipelineReporter.format_summary(report)
        
        assert "PIPELINE EXECUTION SUMMARY" in summary
        assert "Campaign ID: campaign_001" in summary
        assert "Status: SUCCESS" in summary
        assert "Execution Time: 45.50 seconds" in summary
        assert "Products Processed: 2" in summary
        assert "Total Assets: 3" in summary
        assert "Assets Generated: 2" in summary
        assert "Assets Reused: 1" in summary

    def test_format_summary_with_errors(self, failed_result):
        """Test formatting summary includes errors."""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=10)
        
        report = PipelineReporter.generate_report(
            failed_result,
            start_time,
            end_time
        )
        
        summary = PipelineReporter.format_summary(report)
        
        assert "Status: FAILED" in summary
        assert "ERRORS:" in summary
        assert "GenAI API error" in summary
        assert "Network timeout" in summary

    def test_format_summary_with_compliance(self, sample_assets):
        """Test formatting summary includes compliance results."""
        sample_assets[0].compliance_status = ComplianceResult(
            passed=True,
            details="All checks passed",
            violations=[]
        )
        sample_assets[1].compliance_status = ComplianceResult(
            passed=False,
            details="Logo not detected",
            violations=["Missing brand logo", "Wrong color palette"]
        )
        
        result = PipelineResult(
            campaign_id="campaign_001",
            outputs=sample_assets,
            execution_time=45.5,
            success=True,
            errors=[]
        )
        
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=45)
        
        report = PipelineReporter.generate_report(
            result,
            start_time,
            end_time
        )
        
        summary = PipelineReporter.format_summary(report)
        
        assert "COMPLIANCE RESULTS:" in summary
        assert "PASSED" in summary
        assert "FAILED" in summary
        assert "Missing brand logo" in summary
        assert "Wrong color palette" in summary

    def test_generate_report_timestamp_format(self, sample_result):
        """Test report timestamp is in ISO format."""
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime(2024, 1, 1, 10, 0, 45)
        
        report = PipelineReporter.generate_report(
            sample_result,
            start_time,
            end_time
        )
        
        # Verify timestamp is ISO format
        timestamp = report["timestamp"]
        assert "2024-01-01" in timestamp
        assert "10:00:45" in timestamp

    def test_generate_report_empty_outputs(self):
        """Test report generation with no outputs."""
        result = PipelineResult(
            campaign_id="campaign_003",
            outputs=[],
            execution_time=5.0,
            success=False,
            errors=["No products to process"]
        )
        
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=5)
        
        report = PipelineReporter.generate_report(
            result,
            start_time,
            end_time
        )
        
        assert report["summary"]["total_assets"] == 0
        assert report["summary"]["assets_generated"] == 0
        assert report["summary"]["assets_reused"] == 0
        assert report["summary"]["products_processed"] == 0
