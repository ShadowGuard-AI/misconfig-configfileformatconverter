![Banner](banner.png)

# misconfig-ConfigFileFormatConverter
A simple command-line utility to convert configuration files between common formats (e.g., YAML to JSON, TOML to YAML). This helps normalize configurations and facilitates using other analysis tools. Uses `PyYAML`, `toml`, and `json` libraries. - Focused on Check for misconfigurations in configuration files or infrastructure definitions

## Install
`git clone https://github.com/ShadowGuardAI/misconfig-configfileformatconverter`

The output path may not be the input file; naming the same file, in any spelling, is refused at exit 1 and the input is left untouched. An empty input is an error at exit 1, not a conversion. When the input and output formats are the same, no conversion occurs and no file is written; the run exits 1 saying so, instead of rewriting the file in a new layout. A failed conversion leaves no partial output file behind: the result is serialized first and only written out once it is complete.

## Usage
`./misconfig-configfileformatconverter [params]`

## Parameters
- `-h`: Show help message and exit
- `--input_format`: Format of the input file.
- `--output_format`: Format of the output file.

## License
Copyright (c) ShadowGuardAI
