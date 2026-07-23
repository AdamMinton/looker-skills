import looker_sdk
import json
import argparse
import sys

def fetch_scenario(identifier, identifier_type='id', output_file=None, config_file='looker.ini', section='Looker', inject_file=None, inject_key=None):
    """
    Fetches a query's data and config from Looker and formats it for the harness.
    
    Args:
        identifier: The Query ID or Slug.
        identifier_type: 'id' or 'slug'.
        output_file: Optional path to write the JSON output.
        config_file: Path to looker.ini (default: looker.ini)
        section: Section in looker.ini (default: Looker)
    """
    sdk = looker_sdk.init40(config_file=config_file, section=section)
    
    query_id = identifier
    
    # Resolve slug to ID if needed
    if identifier_type == 'slug':
        try:
            query = sdk.query_for_slug(slug=identifier)
            if not query:
                print(f"Error: No query found with slug '{identifier}'")
                return
            query_id = query.id
            print(f"Resolved slug '{identifier}' to Query ID: {query_id}")
        except Exception as e:
            print(f"Error resolving slug: {e}")
            return

    # 1. Get the Query Definition (for Config)
    print(f"Fetching Query Definition ({query_id})...")
    try:
        query_def = sdk.query(query_id=query_id)
    except Exception as e:
        print(f"Error fetching query definition: {e}")
        return

    # 2. Run the Query (for Data & Response)
    print(f"Running Query (json_detail)...")
    try:
        response_json = sdk.run_query(
            query_id=query_id,
            result_format='json_detail'
        )
        # run_query returns a string for json_detail in the python SDK usually, need to parse it
        response = json.loads(response_json)
    except Exception as e:
        print(f"Error running query: {e}")
        return

    # 3. Construct the Scenario Object
    # Harness expects: { config: {}, data: [], queryResponse: { fields: ..., pivots: ... } }
    
    scenario = {
        "config": query_def.vis_config or {},
        "data": response.get('data', []),
        "queryResponse": {
            "fields": response.get('fields', {}),
            "pivots": response.get('pivots', [])
        }
    }
    
    # Optional: Clean up queryResponse to match Viz API strictness if needed
    # (e.g., removing 'dimensions' if they are empty in merged results, matching the 'measure_like' behavior)
    # For now, passing the full fields object is usually safe and helpful.

    output_json = json.dumps(scenario, indent=2)

    if output_file:
        with open(output_file, 'w') as f:
            f.write(output_json)
        print(f"Successfully wrote scenario to {output_file}")
    
    if inject_file:
        inject_into_harness(scenario, inject_file, inject_key or identifier)
    
    if not output_file and not inject_file:
        print(output_json)

def inject_into_harness(scenario_data, js_file_path, scenario_key):
    """
    Appends the scenario to the window.scenarios object in the JS file.
    It parses the JS file (expecting 'window.scenarios = { ... };'), 
    parses the JSON inside, adds the new key, and rewrites the file.
    """
    print(f"Injecting scenario '{scenario_key}' into {js_file_path}...")
    
    try:
        with open(js_file_path, 'r') as f:
            content = f.read()
        
        # Super naive JS parsing: find the start and end of the object
        # Assumes format: window.scenarios = { ... }; 
        prefix = "window.scenarios = "
        start_index = content.find(prefix)
        if start_index == -1:
            print(f"Error: Could not find '{prefix}' in {js_file_path}")
            return

        json_start = start_index + len(prefix)
        # Find the last semicolon which likely ends the statement
        json_end = content.rfind(";")
        if json_end == -1:
            json_end = len(content) # Fallback if no semicolon

        existing_json_str = content[json_start:json_end].strip()
        
        # Safely parse the existing JS object as JSON
        # Note: This requires the JS file content to be valid JSON (keys quoted, etc.)
        # If the existing file has comments or unquoted keys, json.loads will fail.
        # harness/data_scenarios.js usually has strict JSON structure inside the assignment.
        try:
            scenarios = json.loads(existing_json_str)
        except json.JSONDecodeError:
            # If standard JSON fails, we might need a more robust parser or just regex replacement 
            # if the file contains JS-specific syntax (comments, trailing commas).
            # For now, let's try to handle standard JSON structure.
            print("Warning: Could not parse existing scenarios as standard JSON. Attempting simplistic merge...")
            # Fallback: remove the last closing brace '}' and append our new key
            clean_content = existing_json_str.rstrip().rstrip(';')
            if clean_content.endswith('};'): 
                 clean_content = clean_content[:-2]
            elif clean_content.endswith('}'):
                 clean_content = clean_content[:-1]
            
            new_entry = f', "{scenario_key}": {json.dumps(scenario_data)}'
            new_content = content[:json_start] + clean_content + new_entry + "};"
            
            with open(js_file_path, 'w') as f:
                f.write(new_content)
            print(f"Successfully appended '{scenario_key}' to {js_file_path} (Fallback Mode)")
            return

        # key update
        scenarios[scenario_key] = scenario_data
        
        # Re-serialize
        new_json_str = json.dumps(scenarios, indent=2)
        
        # reconstruct file
        new_content = content[:json_start] + new_json_str + ";"
        
        with open(js_file_path, 'w') as f:
            f.write(new_content)
        
        print(f"Successfully injected '{scenario_key}' into {js_file_path}")

    except Exception as e:
        print(f"Error injecting into harness: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch a Looker Query and convert to Harness Scenario.")
    parser.add_argument("identifier", help="The Query ID or Slug")
    parser.add_argument("--type", choices=['id', 'slug'], default='id', help="Type of identifier (default: id)")
    parser.add_argument("--out", help="Output JSON file path")
    parser.add_argument("--config", default="looker.ini", help="Path to looker.ini file")
    parser.add_argument("--section", default="Looker", help="Section in looker.ini to use")
    
    parser.add_argument("--inject", help="Path to harness/data_scenarios.js to inject result")
    parser.add_argument("--key", help="Key name for the scenario in the harness (defaults to identifier)")
    
    args = parser.parse_args()
    
    fetch_scenario(args.identifier, args.type, args.out, args.config, args.section, args.inject, args.key)
