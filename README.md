# Scrbd-Scrpr

Python script for analyzing documents on Scribd using customizable regex patterns. This is for educational purposes only, if you misuse this its on you, dont be a jerk.

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Install chromedriver in the pwd, I have one here but its prolly old by now

## Usage

Run the script with the following command:
```bash
python script.py -s "your search term" -p number_of_pages
```

Example:
```bash
python script.py -s "something idk :P" -p 5
```

## Adding Custom Patterns

The script uses two types of regex patterns for document analysis:

### 1. Primary Patterns

Primary patterns are the main identifiers you're looking for in documents. Add them in the `StatementAnalyzer` class:

```python
self.primary_patterns = [
    r"Pattern1_with_capture_group_(\d+)",
    r"Another_pattern_with_(.*?)_capture",
    r"Simple_pattern_without_capture"
]
```

Tips for primary patterns:
- Use capture groups `()` to extract specific information
- Make patterns as specific as possible to reduce false positives
- Use `\s*` for flexible whitespace matching
- Consider case sensitivity (the script uses re.IGNORECASE by default)

Example primary patterns:
```python
self.primary_patterns = [
    r"ID\s*Number:\s*(\d{6,10})",
    r"Reference:\s*([A-Z]{2}\d{4,8})",
    r"Code:\s*([A-Z0-9]{8,12})"
]
```

### 2. Organization Patterns

Organization patterns verify the context or grouping of the document. Add them like this:

```python
self.organization_patterns = [
    r"Company_name_pattern",
    r"Department_identifier_pattern",
    r"Document_type_pattern"
]
```

Example organization patterns:
```python
self.organization_patterns = [
    r"Department\s+of\s+Finance",
    r"Financial\s+Statement\s+\d{4}",
    r"Quarterly\s+Report"
]
```

### Customizing Validation

You can customize the validation of primary matches by modifying the `_validate_primary_match` method:

```python
def _validate_primary_match(self, matches: List[str]) -> bool:
    """
    Add custom validation logic here
    """
    for match in matches:
        # Example: Ensure match is at least 6 characters
        if len(match) < 6:
            return False
        # Add more validation rules as needed
    return True
```

## Output

The script creates a timestamped directory containing:
- `evidence_summary.csv`: Summary of all matches
- `evidence_N.txt`: Detailed evidence files for each match
- `all_statements.txt`: List of all analyzed URLs

The evidence files contain:
1. The document URL
2. Primary matches found
3. Organization context matches
4. Full document text

## Tips for Pattern Development

1. Start with broad patterns and refine them based on results
2. Test patterns on sample documents first
3. Use regex testing tools to validate patterns
4. Consider common variations in formatting
5. Handle potential special characters
7. Consider multilingual support needed :)

## License

This project is open source and available under the MIT License.
