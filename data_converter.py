import os
import glob
import json
import pandas as pd


def find_candidate_files(root_dir='.'):
    patterns = [os.path.join(root_dir, '*.csv'), os.path.join(root_dir, '*.xlsx'), os.path.join(root_dir, '*.xls')]
    files = []
    for p in patterns:
        files.extend(glob.glob(p))
    return sorted(files)


def try_read_table(path, header_options=(0, 1, 2, 3, 4)):
    for header in header_options:
        try:
            if path.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(path, header=header)
            else:
                df = pd.read_csv(path, header=header)
        except Exception:
            continue
        # require at least one column that looks like a title
        cols = [c.lower().strip() for c in df.columns.astype(str)]
        if any('title' in c or 'name' in c for c in cols):
            return df
    return None


def infer_columns(df):
    mapping = {}
    cols = {c.lower().strip(): c for c in df.columns.astype(str)}

    def find(keys):
        for k in keys:
            for col_lower, col_orig in cols.items():
                if k in col_lower:
                    return col_orig
        return None

    mapping['Title'] = find(['title', 'name'])
    mapping['Author'] = find(['author', 'creator'])
    mapping['Year'] = find(['year', 'date'])
    mapping['Classification'] = find(['class', 'classification', 'callno', 'call number'])
    mapping['Subject'] = find(['subject', 'category', 'genre'])
    return mapping


def normalize_row(row, mapping):
    title = row.get(mapping.get('Title')) if mapping.get('Title') else None
    if pd.isna(title) or title is None:
        return None
    author = row.get(mapping.get('Author')) if mapping.get('Author') else ''
    year = row.get(mapping.get('Year')) if mapping.get('Year') else ''
    classification = row.get(mapping.get('Classification')) if mapping.get('Classification') else ''
    subject = row.get(mapping.get('Subject')) if mapping.get('Subject') else ''

    # Clean
    try:
        year_val = int(year) if pd.notna(year) and str(year).strip() != '' and str(year).strip().isdigit() else 0
    except Exception:
        year_val = 0

    author_val = str(author).strip() if pd.notna(author) else 'Unknown'
    classification_val = str(classification).strip() if pd.notna(classification) else ''
    if pd.isna(subject) or str(subject).strip() == '':
        subjects_val = ['General']
    else:
        # If subject contains commas, split
        subj = str(subject)
        subjects_val = [s.strip() for s in subj.split(',')] if ',' in subj else [subj.strip()]

    return {
        'Title': str(title).strip(),
        'Author': author_val,
        'Subject': subjects_val,
        'Year': year_val,
        'Classification': classification_val
    }


def load_existing_library(path='library_data.json'):
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    # fallback to old file name
    if os.path.exists('library_data'):
        try:
            with open('library_data', 'r') as f:
                return json.load(f)
        except Exception:
            return []
    return []


def main(root_dir='.'):
    print('Scanning for CSV/XLSX files...')
    files = find_candidate_files(root_dir)
    if not files:
        print('No CSV/XLSX files found in the workspace. If you have source files, place them in the project root and re-run this script.')

    all_records = []
    for path in files:
        print(f'Trying: {path}')
        df = try_read_table(path)
        if df is None:
            print(f'  Could not parse {path} (no recognizable header). Skipping.')
            continue
        mapping = infer_columns(df)
        if not mapping.get('Title'):
            print(f'  No title-like column detected in {path}. Skipping.')
            continue

        # Normalize rows
        for _, row in df.iterrows():
            rec = normalize_row(row, mapping)
            if rec:
                all_records.append(rec)
        print(f'  Extracted {len(all_records)} total records so far.')

    existing = load_existing_library()
    before = len(existing)
    # Append only new entries (simple dedupe by Title+Author+Year)
    seen = {(r.get('Title','').lower(), r.get('Author','').lower(), r.get('Year')) for r in existing}
    new_added = 0
    for r in all_records:
        key = (r['Title'].lower(), r['Author'].lower(), r['Year'])
        if key not in seen:
            existing.append(r)
            seen.add(key)
            new_added += 1

    if new_added == 0:
        print(f'No new records found to add. Existing records: {before}')
    else:
        with open('library_data.json', 'w') as f:
            json.dump(existing, f, indent=4)
        print(f'Added {new_added} new records. Total now: {len(existing)}. Saved to library_data.json')


if __name__ == '__main__':
    main('.')
