"""Report generation utilities for the Creative Automation Pipeline."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from ..models import PipelineResult, GeneratedAsset


class PipelineReporter:
    """Generates execution reports for pipeline runs."""
    
    @staticmethod
    def generate_report(
        result: PipelineResult,
        start_time: datetime,
        end_time: datetime,
        output_path: Optional[str] = None
    ) -> dict:
        """
        Generate a comprehensive execution summary report.
        
        Args:
            result: PipelineResult containing execution details
            start_time: Pipeline start timestamp
            end_time: Pipeline end timestamp
            output_path: Optional path to save report as JSON file
        
        Returns:
            Dictionary containing the report data
        """
        # Calculate statistics
        total_assets = len(result.outputs)
        assets_generated = sum(1 for asset in result.outputs if asset.was_generated)
        assets_reused = total_assets - assets_generated
        
        # Get unique products processed
        products_processed = list(set(asset.product_id for asset in result.outputs))
        
        # Collect compliance results if available
        compliance_results = []
        for asset in result.outputs:
            if asset.compliance_status:
                compliance_results.append({
                    "product_id": asset.product_id,
                    "aspect_ratio": asset.aspect_ratio,
                    "passed": asset.compliance_status.passed,
                    "details": asset.compliance_status.details,
                    "violations": asset.compliance_status.violations
                })
        
        # Build report structure
        report = {
            "campaign_id": result.campaign_id,
            "timestamp": end_time.isoformat(),
            "execution_time_seconds": result.execution_time,
            "success": result.success,
            "summary": {
                "products_processed": len(products_processed),
                "product_ids": products_processed,
                "total_assets": total_assets,
                "assets_generated": assets_generated,
                "assets_reused": assets_reused
            },
            "outputs": [
                {
                    "product_id": asset.product_id,
                    "aspect_ratio": asset.aspect_ratio,
                    "file_path": asset.file_path,
                    "was_generated": asset.was_generated
                }
                for asset in result.outputs
            ],
            "errors": result.errors,
            "compliance_results": compliance_results if compliance_results else None
        }
        
        # Save to file if path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
        
        return report
    
    @staticmethod
    def format_summary(report: dict) -> str:
        """
        Format report as human-readable summary text.
        
        Args:
            report: Report dictionary from generate_report()
        
        Returns:
            Formatted summary string
        """
        lines = [
            "=" * 60,
            "PIPELINE EXECUTION SUMMARY",
            "=" * 60,
            f"Campaign ID: {report['campaign_id']}",
            f"Timestamp: {report['timestamp']}",
            f"Status: {'SUCCESS' if report['success'] else 'FAILED'}",
            f"Execution Time: {report['execution_time_seconds']:.2f} seconds",
            "",
            "SUMMARY:",
            f"  Products Processed: {report['summary']['products_processed']}",
            f"  Product IDs: {', '.join(report['summary']['product_ids'])}",
            f"  Total Assets: {report['summary']['total_assets']}",
            f"  Assets Generated: {report['summary']['assets_generated']}",
            f"  Assets Reused: {report['summary']['assets_reused']}",
        ]
        
        if report['errors']:
            lines.extend([
                "",
                "ERRORS:",
            ])
            for error in report['errors']:
                lines.append(f"  - {error}")
        
        if report.get('compliance_results'):
            lines.extend([
                "",
                "COMPLIANCE RESULTS:",
            ])
            for comp in report['compliance_results']:
                status = "PASSED" if comp['passed'] else "FAILED"
                lines.append(f"  - {comp['product_id']} ({comp['aspect_ratio']}): {status}")
                if comp['violations']:
                    for violation in comp['violations']:
                        lines.append(f"    * {violation}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
