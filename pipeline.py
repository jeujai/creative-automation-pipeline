#!/usr/bin/env python3
"""
Creative Automation Pipeline - Main CLI Entry Point

This script provides the command-line interface for the Creative Automation Pipeline.
It processes campaign briefs and generates creative assets across multiple aspect ratios.
"""

import argparse
import sys
import os
import yaml
from pathlib import Path
from typing import Dict, Any

from src.orchestrator import PipelineOrchestrator


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='Creative Automation Pipeline - Generate social media ad assets from campaign briefs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with campaign brief
  python pipeline.py --brief campaign_brief.yaml
  
  # Use custom configuration file
  python pipeline.py --brief campaign_brief.yaml --config custom_config.yaml
  
  # Enable compliance checks
  python pipeline.py --brief campaign_brief.yaml --compliance
  
  # Enable verbose debug logging
  python pipeline.py --brief campaign_brief.yaml --verbose
        """
    )
    
    parser.add_argument(
        '--brief',
        type=str,
        required=True,
        help='Path to campaign brief file (JSON or YAML format)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '--compliance',
        action='store_true',
        help='Enable compliance checks (brand and legal validation)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose debug logging'
    )
    
    return parser.parse_args()


def load_configuration(config_path: str, args: argparse.Namespace) -> Dict[str, Any]:
    """
    Load configuration from file and override with environment variables and CLI arguments.
    
    Args:
        config_path: Path to configuration YAML file
        args: Parsed command-line arguments
    
    Returns:
        Configuration dictionary
    
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    # Check if config file exists
    if not Path(config_path).exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    # Load configuration from YAML file
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if not config:
        raise ValueError(f"Configuration file is empty: {config_path}")
    
    # Override with environment variables
    config = _apply_environment_overrides(config)
    
    # Override with command-line arguments
    config = _apply_cli_overrides(config, args)
    
    return config


def _apply_environment_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply environment variable overrides to configuration.
    
    Environment variables are resolved from ${VAR_NAME} placeholders in the config.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Configuration with environment variables resolved
    """
    # Resolve GenAI API key from environment
    if 'genai' in config and 'api_key' in config['genai']:
        api_key = config['genai']['api_key']
        if isinstance(api_key, str) and api_key.startswith('${') and api_key.endswith('}'):
            env_var = api_key[2:-1]  # Extract variable name
            config['genai']['api_key'] = os.environ.get(env_var, '')
    
    # Allow environment variable overrides for key settings
    if 'PIPELINE_INPUT_DIR' in os.environ:
        config.setdefault('storage', {})['input_dir'] = os.environ['PIPELINE_INPUT_DIR']
    
    if 'PIPELINE_OUTPUT_DIR' in os.environ:
        config.setdefault('storage', {})['output_dir'] = os.environ['PIPELINE_OUTPUT_DIR']
    
    if 'PIPELINE_LOG_LEVEL' in os.environ:
        config.setdefault('logging', {})['level'] = os.environ['PIPELINE_LOG_LEVEL']
    
    return config


def _apply_cli_overrides(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    """
    Apply command-line argument overrides to configuration.
    
    Args:
        config: Configuration dictionary
        args: Parsed command-line arguments
    
    Returns:
        Configuration with CLI overrides applied
    """
    # Override compliance setting
    if args.compliance:
        config.setdefault('compliance', {})['enabled'] = True
    
    # Override logging level for verbose mode
    if args.verbose:
        config.setdefault('logging', {})['level'] = 'DEBUG'
    
    return config


def validate_configuration(config: Dict[str, Any]) -> None:
    """
    Validate required configuration settings.
    
    Args:
        config: Configuration dictionary
    
    Raises:
        ValueError: If required configuration is missing or invalid
    """
    # Validate GenAI configuration
    if 'genai' not in config:
        raise ValueError("Configuration missing 'genai' section")
    
    genai_config = config['genai']
    
    if not genai_config.get('api_key'):
        raise ValueError(
            "GenAI API key not configured. "
            "Set OPENAI_API_KEY environment variable or update config.yaml"
        )
    
    if not genai_config.get('provider'):
        raise ValueError("GenAI provider not specified in configuration")
    
    # Validate storage configuration
    if 'storage' not in config:
        raise ValueError("Configuration missing 'storage' section")
    
    storage_config = config['storage']
    
    if not storage_config.get('input_dir'):
        raise ValueError("Input directory not specified in configuration")
    
    if not storage_config.get('output_dir'):
        raise ValueError("Output directory not specified in configuration")
    
    # Create directories if they don't exist
    input_dir = Path(storage_config['input_dir'])
    output_dir = Path(storage_config['output_dir'])
    
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Validate aspect ratios
    if 'aspect_ratios' not in config or not config['aspect_ratios']:
        raise ValueError("No aspect ratios specified in configuration")
    
    # Validate compliance configuration if enabled
    if config.get('compliance', {}).get('enabled', False):
        compliance_config = config['compliance']
        
        if 'brand' in compliance_config:
            logo_template = compliance_config['brand'].get('logo_template')
            if logo_template and not Path(logo_template).exists():
                print(f"Warning: Brand logo template not found: {logo_template}")
        
        if 'legal' not in compliance_config:
            print("Warning: Compliance enabled but no legal configuration provided")


def print_summary(result) -> None:
    """
    Print execution summary to console.
    
    Args:
        result: PipelineResult object
    """
    print("\n" + "="*60)
    print("PIPELINE EXECUTION SUMMARY")
    print("="*60)
    print(f"Campaign ID: {result.campaign_id}")
    print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Execution Time: {result.execution_time:.2f} seconds")
    print(f"Assets Generated: {len(result.outputs)}")
    
    if result.outputs:
        generated_count = sum(1 for asset in result.outputs if asset.was_generated)
        reused_count = len(result.outputs) - generated_count
        print(f"  - Generated: {generated_count}")
        print(f"  - Reused: {reused_count}")
    
    if result.errors:
        print(f"\nErrors: {len(result.errors)}")
        for error in result.errors:
            print(f"  - {error}")
    
    print("="*60 + "\n")


def main() -> int:
    """
    Main entry point for the pipeline.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Parse command-line arguments
        args = parse_arguments()
        
        # Validate brief file exists
        if not Path(args.brief).exists():
            print(f"Error: Campaign brief file not found: {args.brief}", file=sys.stderr)
            return 1
        
        # Load and validate configuration
        print(f"Loading configuration from: {args.config}")
        config = load_configuration(args.config, args)
        
        print("Validating configuration...")
        validate_configuration(config)
        
        # Initialize pipeline orchestrator
        print("Initializing pipeline orchestrator...")
        orchestrator = PipelineOrchestrator(config)
        
        # Execute pipeline
        print(f"\nProcessing campaign brief: {args.brief}")
        print("-" * 60)
        result = orchestrator.run(args.brief)
        
        # Print summary
        print_summary(result)
        
        # Return appropriate exit code
        return 0 if result.success else 1
        
    except FileNotFoundError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1
    
    except ValueError as e:
        print(f"Configuration Error: {str(e)}", file=sys.stderr)
        return 1
    
    except yaml.YAMLError as e:
        print(f"Configuration Parse Error: {str(e)}", file=sys.stderr)
        return 1
    
    except KeyboardInterrupt:
        print("\nPipeline execution interrupted by user", file=sys.stderr)
        return 1
    
    except Exception as e:
        print(f"Unexpected Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
