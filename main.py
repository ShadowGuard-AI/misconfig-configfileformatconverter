import argparse
import json
import logging
import sys

try:
    import yaml
    from yaml.loader import SafeLoader
except ImportError:
    print("PyYAML is not installed. Please install it using: pip install PyYAML")
    sys.exit(1)

try:
    import toml
except ImportError:
    print("TOML is not installed. Please install it using: pip install toml")
    sys.exit(1)


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description="Convert configuration files between common formats (YAML, JSON, TOML).")
    parser.add_argument("input_file", help="Path to the input configuration file.")
    parser.add_argument("output_file", help="Path to the output configuration file.")
    parser.add_argument("--input_format", choices=['yaml', 'json', 'toml'], required=True, help="Format of the input file.")
    parser.add_argument("--output_format", choices=['yaml', 'json', 'toml'], required=True, help="Format of the output file.")
    return parser

def load_file(file_path, file_format):
    """
    Loads the configuration file based on the specified format.

    Args:
        file_path (str): Path to the configuration file.
        file_format (str): Format of the configuration file (yaml, json, toml).

    Returns:
        dict: A dictionary representing the configuration data.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If there's an issue parsing the file content.
    """
    try:
        with open(file_path, 'r') as f:
            if file_format == 'yaml':
                try:
                    data = yaml.load(f, Loader=SafeLoader)
                except yaml.YAMLError as e:
                    raise ValueError(f"Error parsing YAML file: {e}")
            elif file_format == 'json':
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Error parsing JSON file: {e}")
            elif file_format == 'toml':
                try:
                    data = toml.load(f)
                except toml.TomlDecodeError as e:
                    raise ValueError(f"Error parsing TOML file: {e}")
            else:
                raise ValueError(f"Unsupported input format: {file_format}")
        return data
    except FileNotFoundError:
        logging.error(f"Input file not found: {file_path}")
        raise
    except ValueError as e:
        logging.error(e)
        raise


def write_file(data, file_path, file_format):
    """
    Writes the configuration data to the output file based on the specified format.

    Args:
        data (dict): The configuration data to write.
        file_path (str): Path to the output configuration file.
        file_format (str): Format of the output file (yaml, json, toml).

    Raises:
        ValueError: If there's an issue writing the file content.
    """
    try:
        with open(file_path, 'w') as f:
            if file_format == 'yaml':
                try:
                    yaml.dump(data, f, indent=2)  # Use indent for readability
                except yaml.YAMLError as e:
                    raise ValueError(f"Error writing YAML file: {e}")
            elif file_format == 'json':
                try:
                    json.dump(data, f, indent=2)  # Use indent for readability
                except TypeError as e:
                     raise ValueError(f"Error writing JSON file: {e}")
            elif file_format == 'toml':
                try:
                    toml.dump(data, f)
                except toml.TomlEncodeError as e:
                    raise ValueError(f"Error writing TOML file: {e}")
            else:
                raise ValueError(f"Unsupported output format: {file_format}")
    except ValueError as e:
        logging.error(e)
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise

def main():
    """
    Main function to execute the configuration file conversion.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    # Input validation: Check if input and output formats are the same.
    if args.input_format == args.output_format:
        logging.warning("Input and output formats are the same.  No conversion will occur.")

    try:
        # Load the input file
        data = load_file(args.input_file, args.input_format)

        # Write to the output file
        write_file(data, args.output_file, args.output_format)

        logging.info(f"Successfully converted {args.input_file} ({args.input_format}) to {args.output_file} ({args.output_format}).")

    except FileNotFoundError:
        sys.exit(1)  # Exit code 1 indicates an error
    except ValueError:
        sys.exit(1) # Exit code 1 indicates an error
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)
if __name__ == "__main__":
    # Usage examples:
    # 1. Convert YAML to JSON: python main.py config.yaml config.json --input_format yaml --output_format json
    # 2. Convert TOML to YAML: python main.py config.toml config.yaml --input_format toml --output_format yaml
    # 3. Convert JSON to TOML: python main.py config.json config.toml --input_format json --output_format toml
    main()