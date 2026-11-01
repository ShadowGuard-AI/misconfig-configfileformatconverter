import argparse
import json
import logging
import os
import sys
import tempfile

try:
    import yaml
    from yaml.loader import SafeLoader
except ImportError:
    print("PyYAML is not installed. Please install it using: pip install PyYAML")
    # These import guards run before argparse exists, so on a
    # machine missing either library even a --help call prints the
    # install line and exits 1. There is no way to read my usage
    # text without the dependencies installed.
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
            # The format comes from the required flags alone. The file
            # names are never consulted, so a document named .json is
            # parsed as YAML when the flag says yaml, and nothing warns
            # about the disagreement.
            if file_format == 'yaml':
                try:
                    # SafeLoader turns YAML timestamps into datetime objects and
                    # yes and no into booleans. Converting such a file to JSON
                    # then fails in write_file, because JSON has no datetime, and
                    # converting it to YAML writes the values back in a different
                    # spelling than the file I read. The data survives; the text
                    # does not, and some of it does not survive at all.
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
    # Serialize fully to text first. A value the target format cannot
    # hold fails here, before any output file is touched, so a failed
    # conversion never leaves a partial file behind.
    try:
        if file_format == 'yaml':
            try:
                # yaml.dump sorts keys by default, so a YAML output from me
                # is in alphabetical order whatever order the input used,
                # while the JSON dump below keeps the input order. The same
                # conversion therefore preserves ordering in one direction
                # and not in another.
                text = yaml.dump(data, indent=2)
            except yaml.YAMLError as e:
                raise ValueError(f"Error writing YAML file: {e}")
        elif file_format == 'json':
            try:
                text = json.dumps(data, indent=2)
            except TypeError as e:
                raise ValueError(f"Error writing JSON file: {e}")
        elif file_format == 'toml':
            try:
                # TOML needs a mapping at the top and string keys throughout.
                # A YAML or JSON file holding a top level list, or integer
                # keys, loads fine and then fails here, as one ValueError
                # for the whole conversion, with no hint which key caused it.
                text = toml.dumps(data)
            except Exception as e:
                raise ValueError(f"Error writing TOML file: {e}")
        else:
            raise ValueError(f"Unsupported output format: {file_format}")
    except ValueError as e:
        logging.error(e)
        raise

    # Write to a temporary sibling and rename on success, so the
    # output path only ever holds a complete conversion.
    directory = os.path.dirname(os.path.abspath(file_path))
    # The temporary file arrives with mkstemp permissions, owner
    # only, and os.replace keeps those permissions on the result.
    # A converted config can therefore come out harder to read
    # for the service that needs it than the file it replaces,
    # which surprises people who check content and not modes.
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".convert-", suffix=".tmp")
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(text)
        os.replace(tmp_path, file_path)
    except Exception as e:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        logging.error(f"An unexpected error occurred: {e}")
        raise

def main():
    """
    Main function to execute the configuration file conversion.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    # The output may never be the input file, in any spelling.
    if os.path.exists(args.input_file) and os.path.exists(args.output_file):
        same = os.path.realpath(args.input_file) == os.path.realpath(args.output_file)
    else:
        # When the output does not exist yet I compare spellings, not
        # real paths, so an output reached through a symlink to the
        # input under a different name is not caught by this check.
        # The rename in write_file would replace the link itself
        # rather than the input, which limits the damage, but the
        # converted result would not be where the operator expects.
        same = os.path.abspath(args.input_file) == os.path.abspath(args.output_file)
    if same:
        logging.error("Output path is the input file; refusing to overwrite it. Nothing was converted.")
        sys.exit(1)

    # Same format means no conversion happens, and no file is written.
    # The old code warned about that and then rewrote the file anyway.
    if args.input_format == args.output_format:
        logging.error("Input and output formats are the same. No conversion will occur, and no file has been written.")
        sys.exit(1)

    try:
        # An empty input holds nothing to convert.
        with open(args.input_file, 'r') as f:
            raw = f.read()
        if raw.strip() == "":
            logging.error("Input file is empty. Nothing was converted.")
            sys.exit(1)

        # Load the input file
        data = load_file(args.input_file, args.input_format)
        if data is None:
            logging.error("Input file parsed to nothing. Nothing was converted.")
            sys.exit(1)

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