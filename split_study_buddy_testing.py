#!/usr/bin/env python3
"""
Script to split the consolidated study-buddy-testing.txt file into individual test files.
Usage mirrors split_study_buddy.py with DRY RUN by default.

Consolidated file format:

  ## study-buddy-tests/<relative/output/path>
  ```<lang>
  ...file contents...
  ```

Example:

  ## study-buddy-tests/e2e/critical/critical-paths.test.ts
  ```ts
  describe('Critical User Paths', () => { /* ... */ });
  ```
"""

import os
import argparse
from pathlib import Path
from typing import List, Dict


class StudyBuddyTestingSplitter:
    def __init__(self, input_file: str, output_dir: str = "study-buddy-tests", header_prefix: str = "## study-buddy-tests/", dry_run: bool = True):
        self.input_file = input_file
        self.output_dir = output_dir
        self.header_prefix = header_prefix
        self.dry_run = dry_run
        self.files_to_create: List[Dict[str, str]] = []
        self.current_file: str | None = None
        self.current_content: List[str] = []
        self.line_number: int = 0

    def parse_file(self):
        print(f"{'[DRY RUN] ' if self.dry_run else ''}Parsing {self.input_file}...")
        with open(self.input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        in_file_content = False
        code_block_delimiter_count = 0

        for i, line in enumerate(lines):
            self.line_number = i + 1

            # Start of a new embedded file section
            if line.startswith(self.header_prefix):
                # Save previous file if any
                if self.current_file:
                    self._save_current_file()

                file_path = line[len(self.header_prefix):].strip()
                self.current_file = file_path
                self.current_content = []
                in_file_content = False
                code_block_delimiter_count = 0
                continue

            # Separator lines are ignored
            if line.strip() == '---' and self.current_file:
                continue

            # Track fenced code blocks (```)
            if line.strip().startswith('```') and self.current_file:
                code_block_delimiter_count += 1
                # First fence after header starts content (skip the fence line itself)
                if code_block_delimiter_count == 1:
                    in_file_content = True
                    continue
                # Second fence ends content
                if code_block_delimiter_count == 2:
                    in_file_content = False
                    continue

            # Collect content within the first fenced block
            if in_file_content and self.current_file:
                self.current_content.append(line)

        # Save last pending file
        if self.current_file:
            self._save_current_file()

    def _save_current_file(self):
        if not self.current_file or not self.current_content:
            return
        self.files_to_create.append({
            'path': os.path.join(self.output_dir, self.current_file),
            'content': ''.join(self.current_content).rstrip() + '\n',
            'line_start': self.line_number - len(self.current_content) - 2,  # approx
        })

    def create_files(self):
        print(f"\n{'[DRY RUN] ' if self.dry_run else ''}Processing {len(self.files_to_create)} files...\n")
        created_dirs = set()
        for file_info in self.files_to_create:
            file_path = Path(file_info['path'])
            dir_path = file_path.parent

            if dir_path not in created_dirs and str(dir_path) != '.':
                if self.dry_run:
                    print(f"[DRY RUN] Would create directory: {dir_path}")
                else:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    print(f"Created directory: {dir_path}")
                created_dirs.add(dir_path)

            content_preview = file_info['content'][:100].replace('\n', '\\n')
            if len(file_info['content']) > 100:
                content_preview += "..."

            if self.dry_run:
                print(f"[DRY RUN] Would create file: {file_path}")
                print(f"          Size: {len(file_info['content'])} bytes")
                print(f"          Preview: {content_preview}")
                print(f"          Source lines: around {file_info['line_start']}")
                print()
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_info['content'])
                print(f"Created file: {file_path} ({len(file_info['content'])} bytes)")

    def analyze_structure(self):
        print(f"\n{'[DRY RUN] ' if self.dry_run else ''}Project Structure Analysis:")
        print("=" * 60)
        dirs: Dict[str, List[str]] = {}
        for file_info in self.files_to_create:
            dir_path = os.path.dirname(file_info['path'])
            dirs.setdefault(dir_path, []).append(os.path.basename(file_info['path']))
        for dir_path in sorted(dirs.keys()):
            level = dir_path.count(os.sep)
            indent = "  " * level
            dir_name = os.path.basename(dir_path) if dir_path else "study-buddy-tests (root)"
            print(f"{indent}{dir_name}/")
            for file_name in sorted(dirs[dir_path]):
                print(f"{indent}  {file_name}")

        print("\nSummary:")
        print(f"  Total files: {len(self.files_to_create)}")
        print(f"  Total directories: {len(dirs)}")

    def validate_extraction(self):
        print(f"\n{'[DRY RUN] ' if self.dry_run else ''}Validation Results:")
        print("=" * 60)
        issues: List[str] = []
        empty_files = [f['path'] for f in self.files_to_create if not f['content'].strip()]
        if empty_files:
            issues.append(f"Empty files detected: {', '.join(empty_files)}")
        paths = [f['path'] for f in self.files_to_create]
        duplicates = [p for p in paths if paths.count(p) > 1]
        if duplicates:
            issues.append(f"Duplicate file paths: {', '.join(sorted(set(duplicates)))}")
        if issues:
            print("⚠️  Issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✅ No issues found!")

    def run(self):
        try:
            self.parse_file()
            self.analyze_structure()
            self.validate_extraction()
            self.create_files()
            if self.dry_run:
                print(f"\n[DRY RUN COMPLETE] No files were created.")
                print(f"To actually create the files, run without --dry-run or pass --create")
            else:
                print(f"\n✅ Successfully created {len(self.files_to_create)} files!")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            if self.line_number:
                print(f"   Last processed line: {self.line_number}")
            raise


def main():
    parser = argparse.ArgumentParser(
        description='Split consolidated study-buddy testing file into individual test files'
    )
    parser.add_argument('input_file', nargs='?', default='study-buddy-testing.txt', help='Input file (default: study-buddy-testing.txt)')
    parser.add_argument('-o', '--output-dir', default='study-buddy-tests', help='Output directory (default: study-buddy-tests)')
    parser.add_argument('--header-prefix', default='## study-buddy-tests/', help='Header prefix marking file sections')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Show actions without creating files (default: True)')
    parser.add_argument('--create', action='store_true', help='Actually create files (overrides --dry-run)')

    args = parser.parse_args()
    if args.create:
        args.dry_run = False

    if not os.path.exists(args.input_file):
        print(f"❌ Error: Input file '{args.input_file}' not found!")
        return 1

    splitter = StudyBuddyTestingSplitter(
        input_file=args.input_file,
        output_dir=args.output_dir,
        header_prefix=args.header_prefix,
        dry_run=args.dry_run,
    )
    splitter.run()
    return 0


if __name__ == '__main__':
    exit(main())


