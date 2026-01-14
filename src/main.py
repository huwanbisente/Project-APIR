import argparse
import os
from src.pipeline import Pipeline
from dotenv import load_dotenv

# Load env file if exists
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="AI-Assisted Invoice Processing System")
    parser.add_argument("--input", default="input_data", help="Path to input file or directory (default: input_data)")
    parser.add_argument("--output", default="output_data/results.csv", help="Path to output CSV (default: output_data/results.csv)")
    parser.add_argument("--mock", action="store_true", help="Use Mock LLM to save costs/testing")
    
    args = parser.parse_args()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not args.mock and not api_key:
        print("WARNING: No OPENAI_API_KEY found. Defaulting to MOCK mode.")
        args.mock = True

    pipeline = Pipeline(use_mock=args.mock, openai_api_key=api_key)
    
    files_to_process = []
    if os.path.isdir(args.input):
        for root, _, files in os.walk(args.input):
            for file in files:
                if file.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.txt')):
                    files_to_process.append(os.path.join(root, file))
    elif os.path.isfile(args.input):
         files_to_process.append(args.input)
    else:
        print(f"Input path not found: {args.input}")
        return

    if not files_to_process:
        print(f"No valid files found in {args.input}")
        return

    print(f"Found {len(files_to_process)} files to process.")
    
    all_results = []
    for file_path in files_to_process:
        try:
            results = pipeline.process_file(file_path)
            all_results.extend(results)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    try:
        # Save JSON first (Robust backup)
        json_output = args.output.replace('.csv', '.json')
        pipeline.save_to_json(all_results, json_output)

        # Then try CSV
        pipeline.save_to_csv(all_results, args.output)
    except Exception as e:
        print(f"Fatal Error saving results: {e}")

if __name__ == "__main__":
    main()
