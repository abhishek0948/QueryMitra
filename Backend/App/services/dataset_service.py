import pandas as pd
import os
import json
import pdfplumber
from flask import current_app

# OCR dependencies (Strategy 4 — scanned PDFs)
# These are imported lazily inside the methods so the rest of the app
# continues to work even if the system packages are not yet installed.
try:
    import pytesseract
    from pdf2image import convert_from_path
    _OCR_AVAILABLE = True
except ImportError:
    _OCR_AVAILABLE = False
from App.models.dataset import Dataset

class DatasetService:
    def __init__(self):
        self.db = current_app.db
        
    def get_all_datasets(self, user_id=None):
        try:
            if isinstance(self.db, dict):
                # Handle fallback dictionary case
                all_datasets = self.db.get("datasets", [])
                if user_id:
                    return [d for d in all_datasets if d.get('user_id') == user_id]
                return all_datasets
            else:
                # Normal MongoDB case
                query = {'user_id': user_id} if user_id else {}
                datasets = list(self.db.datasets.find(query, {'_id': 0}))
                return datasets
        except Exception as e:
            print(f"Error getting datasets: {str(e)}")
            return []
        
    def _read_file_as_dataframe(self, file_path):
        """Read a CSV or PDF file and return a pandas DataFrame."""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.csv':
            return pd.read_csv(file_path)

        elif ext == '.pdf':
            return self._extract_tables_from_pdf(file_path)

        else:
            raise ValueError(f"Unsupported file format '{ext}'. Please upload a CSV or PDF file.")

    def _extract_tables_from_pdf(self, file_path):
        """
        Extract tabular data from a PDF using a 3-strategy cascade:

          Strategy 1 – Border-based  : pdfplumber default (PDFs with drawn grid lines)
          Strategy 2 – Text-strategy : pdfplumber text-position detection (word-processor
                                       tables that have no visible borders)
          Strategy 3 – Word-position : Groups raw words by their x0 coordinates into
                                       columns. Handles purely whitespace-aligned text
                                       like "Day  Product_A_Sales  Product_B_Sales …"
                                       even when there is a title/heading row above the
                                       actual column headers.
        """
        # ── Strategy 1: border-based ───────────────────────────────────────────
        all_frames = self._try_border_extraction(file_path)
        if all_frames:
            return self._finalize(all_frames)

        # ── Strategy 2: pdfplumber text-strategy ──────────────────────────────
        # Falls back to Strategy 3 on a per-page basis when column names look
        # fragmented (a known artefact of character-spaced PDF fonts).
        all_frames = self._try_text_strategy_extraction(file_path)
        if all_frames:
            return self._finalize(all_frames)

        # ── Strategy 3: raw word-position parsing ─────────────────────────────
        all_frames = self._try_word_position_extraction(file_path)
        if all_frames:
            return self._finalize(all_frames)

        # ── Strategy 4: OCR (scanned / image-only PDFs) ───────────────────────
        # Only attempted when no text layer was found by strategies 1-3 AND
        # the OCR libraries are available on the system.
        if self._is_scanned_pdf(file_path):
            if not _OCR_AVAILABLE:
                raise ValueError(
                    "This appears to be a scanned PDF (no embedded text found). "
                    "OCR support requires the 'pdf2image' and 'pytesseract' packages "
                    "and the Tesseract binary. Please install them and retry."
                )
            all_frames = self._try_ocr_extraction(file_path)
            if all_frames:
                return self._finalize(all_frames)

        raise ValueError(
            "No tables were found in the PDF. "
            "Please make sure the PDF contains structured tabular data "
            "(with or without visible borders)."
        )

    # ── Strategy helpers ──────────────────────────────────────────────────────

    def _try_border_extraction(self, file_path):
        """Strategy 1: use pdfplumber's default (line/border) table detector."""
        frames = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                for table in (page.extract_tables() or []):
                    df = self._table_to_df(table)
                    if df is not None:
                        frames.append(df)
        return frames

    def _try_text_strategy_extraction(self, file_path):
        """
        Strategy 2: pdfplumber text-position strategy (no borders needed).

        For each page, if the extracted frame has fragmented/garbled column
        names (a known artefact of character-spaced fonts), we fall back to
        Strategy 3 (word-position) for that specific page.
        """
        settings = {
            "vertical_strategy":   "text",
            "horizontal_strategy": "text",
            "snap_tolerance":       5,
            "join_tolerance":       5,
            "min_words_vertical":   2,
            "min_words_horizontal": 2,
        }
        frames = []
        last_headers = None   # column names carried forward from the previous page
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_frames = []
                for table in (page.extract_tables(table_settings=settings) or []):
                    df = self._table_to_df(table)
                    if df is not None:
                        page_frames.append(df)
                    elif last_headers is not None:
                        # Page has no detectable header — use columns from the
                        # last successful page (headers only on page 1 pattern).
                        df = self._table_to_df_headerless(table, last_headers)
                        if df is not None:
                            page_frames.append(df)

                # Validate quality: if any frame on this page has garbled
                # column names, fall back to word-position for the whole page.
                if page_frames and all(self._is_quality_frame(f) for f in page_frames):
                    frames.extend(page_frames)
                    last_headers = list(page_frames[-1].columns)
                elif page_frames:
                    # Strategy 3 fallback for this page only
                    words = page.extract_words(
                        x_tolerance=3, y_tolerance=5,
                        keep_blank_chars=False, use_text_flow=False
                    )
                    if words:
                        df = self._words_to_dataframe(words, fallback_headers=last_headers)
                        if df is not None:
                            frames.append(df)
                            last_headers = list(df.columns)
                else:
                    # Strategy 2 found no tables at all on this page.
                    # Try word-position with carried-forward headers.
                    if last_headers is not None:
                        words = page.extract_words(
                            x_tolerance=3, y_tolerance=5,
                            keep_blank_chars=False, use_text_flow=False
                        )
                        if words:
                            df = self._words_to_dataframe(words, fallback_headers=last_headers)
                            if df is not None:
                                frames.append(df)
        return frames

    @staticmethod
    def _is_quality_frame(df):
        """
        Return True if the DataFrame's column names look like real identifiers
        rather than pdfplumber character-split fragments.

        Heuristics that flag a BAD frame:
          • More than 30 % of column names contain an embedded space AND
            that space is surrounded by word characters on both sides
            (e.g. 'y Product_A_Sal', 'ale', 'es Product_B_S') — these are
            fragments of split identifiers, NOT legitimate multi-word names.
          • The average column name length is very short (< 3 characters),
            suggesting many cells are just stray letters.
        """
        import re
        cols = list(df.columns)
        if not cols:
            return False

        # Check for embedded-space fragments: name contains a space AND
        # at least one side is purely alphabetic with no punctuation —
        # typical of pdfplumber character splits.
        fragment_pattern = re.compile(r'\b[a-zA-Z]{1,4}\s+[A-Za-z_]|[A-Za-z_]\s+[a-zA-Z]{1,4}\b')
        n_fragments = sum(1 for c in cols if fragment_pattern.search(c))
        if n_fragments / len(cols) > 0.30:
            return False

        # Average column name too short → likely split characters
        avg_len = sum(len(c) for c in cols) / len(cols)
        if avg_len < 3:
            return False

        return True

    # ── Strategy 4 helpers ────────────────────────────────────────────────────

    @staticmethod
    def _is_scanned_pdf(file_path):
        """
        Return True when the PDF has no usable embedded text on ANY page,
        which is the hallmark of a scanned / image-only PDF.

        We use pdfplumber's extract_words() as the cheapest probe: if the
        total word count across all pages is zero (or negligibly small),
        we conclude the document is image-only and needs OCR.
        """
        total_words = 0
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    words = page.extract_words() or []
                    total_words += len(words)
                    if total_words > 5:   # short-circuit: definitely has text
                        return False
        except Exception:
            pass
        return total_words <= 5

    def _try_ocr_extraction(self, file_path):
        """
        Strategy 4: OCR-based extraction for scanned / image-only PDFs.

        Pipeline per page:
          1. pdf2image converts the page to a high-resolution PIL image.
          2. pytesseract runs Tesseract in hOCR mode to get each word's
             bounding box (x0, top, x1, bottom, text).
          3. The word list is fed directly into _words_to_dataframe(),
             which already handles column clustering and header detection.

        This reuses all the existing column-alignment and header-detection
        logic — no duplication needed.
        """
        frames = []
        last_headers = None

        try:
            # 300 DPI gives Tesseract enough resolution to read small fonts
            images = convert_from_path(file_path, dpi=300)
        except Exception as e:
            raise ValueError(f"Failed to render PDF pages for OCR: {e}")

        for img in images:
            # Run Tesseract; get detailed per-word bounding boxes
            try:
                ocr_data = pytesseract.image_to_data(
                    img,
                    output_type=pytesseract.Output.DICT,
                    config='--psm 6'   # Assume a single block of text (table)
                )
            except Exception as e:
                # Non-fatal: skip pages Tesseract cannot process
                print(f"[OCR] Warning: Tesseract failed on a page — {e}")
                continue

            # Build a word list compatible with pdfplumber's extract_words format
            words = []
            n_boxes = len(ocr_data['text'])
            for i in range(n_boxes):
                text = ocr_data['text'][i].strip()
                conf = int(ocr_data['conf'][i])
                # Skip low-confidence or empty detections
                if not text or conf < 30:
                    continue
                x0   = float(ocr_data['left'][i])
                top  = float(ocr_data['top'][i])
                w    = float(ocr_data['width'][i])
                h    = float(ocr_data['height'][i])
                words.append({
                    'text':   text,
                    'x0':     x0,
                    'top':    top,
                    'x1':     x0 + w,
                    'bottom': top + h,
                })

            if not words:
                continue

            df = self._words_to_dataframe(words, fallback_headers=last_headers)
            if df is not None:
                frames.append(df)
                last_headers = list(df.columns)

        return frames

    def _try_word_position_extraction(self, file_path):
        """
        Strategy 3: group words by their horizontal (x0) positions to reconstruct
        columns, then identify the first row where every cell is a valid column
        name (not a purely-numeric title row) as the header.

        Carries forward the last successfully identified headers so that pages
        containing only data rows (no repeated header) are still captured.
        """
        frames = []
        last_headers = None   # column names carried forward from the previous page
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                words = page.extract_words(
                    x_tolerance=3, y_tolerance=5,
                    keep_blank_chars=False, use_text_flow=False
                )
                if not words:
                    continue

                df = self._words_to_dataframe(words, fallback_headers=last_headers)
                if df is not None:
                    frames.append(df)
                    last_headers = list(df.columns)
        return frames

    def _words_to_dataframe(self, words, fallback_headers=None):
        """
        Convert a flat list of word dicts (from pdfplumber extract_words) into a
        DataFrame by clustering x0 values → columns and top values → rows.

        fallback_headers: if provided and no header row is found on this page
            (all rows are numeric — "headers only on page 1" pattern), these
            column names are used and every row is treated as a data row.
        """
        import math

        # ── 1. Group words into logical rows by their vertical (top) position ─
        row_gap = 8   # pixels; words within this vertical distance share a row
        rows_by_top = {}
        for w in words:
            top = round(float(w['top']))
            # find an existing row bucket within row_gap
            matched = None
            for existing_top in rows_by_top:
                if abs(existing_top - top) <= row_gap:
                    matched = existing_top
                    break
            if matched is None:
                rows_by_top[top] = []
                matched = top
            rows_by_top[matched].append(w)

        # Sort rows top-to-bottom
        sorted_tops = sorted(rows_by_top.keys())
        if len(sorted_tops) < 2:
            return None   # need at least a header + one data row

        # ── 2. Detect column zones from the densest row ──────────────────────
        # Use the row that has the most words as the candidate header
        header_top = max(sorted_tops, key=lambda t: len(rows_by_top[t]))
        header_words = sorted(rows_by_top[header_top], key=lambda w: float(w['x0']))

        # Column zone boundaries: put the cut line in the whitespace gap between
        # adjacent header words. Using the midpoint between header[k].x1 and
        # header[k+1].x0 is most robust — it's always in the actual whitespace.
        # Falls back to midpoint of x0 values when columns are very close.
        boundaries = [0.0]
        for k in range(len(header_words) - 1):
            gap_start = float(header_words[k]['x1'])
            gap_end   = float(header_words[k + 1]['x0'])
            cut = (gap_start + gap_end) / 2.0 if gap_end > gap_start else (gap_start + gap_end) / 2.0
            boundaries.append(cut)
        boundaries.append(float('inf'))   # right sentinel

        def assign_col(w):
            """Return column index: find the rightmost boundary <= word's x0."""
            x0 = float(w['x0'])
            for ci in range(len(boundaries) - 2, -1, -1):
                if x0 >= boundaries[ci]:
                    return ci
            return 0

        # ── 3. Build a 2-D grid ───────────────────────────────────────────────
        grid = []  # list of dicts: {col_index: text}
        for top in sorted_tops:
            row_words = sorted(rows_by_top[top], key=lambda w: float(w['x0']))
            cell_map = {}
            for w in row_words:
                ci = assign_col(w)
                cell_map[ci] = cell_map.get(ci, '') + (' ' if ci in cell_map else '') + w['text']
            grid.append(cell_map)

        n_cols = len(header_words)

        # ── 4. Find the header row (first row where NO cell looks like a lone ─
        #        number or a title string wider than the column count)
        header_row_idx = None
        for i, cell_map in enumerate(grid):
            # Skip rows that are completely numeric (index rows / title numbers)
            values = [cell_map.get(c, '').strip() for c in range(n_cols)]
            non_empty = [v for v in values if v]
            if not non_empty:
                continue
            all_numeric = all(self._is_numeric(v) for v in non_empty)
            if all_numeric:
                continue
            # Skip if this row has only 1 word and looks like a title
            if len(non_empty) == 1 and len(grid) > i + 1:
                continue
            header_row_idx = i
            break

        if header_row_idx is None:
            if fallback_headers is None or len(fallback_headers) != n_cols:
                # No header on this page and no fallback available → skip.
                return None
            # Use the carried-forward headers; treat every non-blank grid row
            # as a data row (the whole page is continuation data).
            headers = list(fallback_headers)
            header_row_idx = -1   # sentinel: all rows are data rows
        else:
            # Build column names from the detected header row
            headers = [grid[header_row_idx].get(c, f'col_{c}').strip() or f'col_{c}'
                       for c in range(n_cols)]

        # ── 5. Data rows follow the header ────────────────────────────────────
        import re
        _footer_re = re.compile(
            r'^\s*(page\s*\d+(\s+of\s+\d+)?|\d+\s*/\s*\d+|\d+)\s*$', re.I
        )
        data_rows = []
        for cell_map in grid[header_row_idx + 1:]:
            row = [cell_map.get(c, '').strip() for c in range(n_cols)]
            if not any(v for v in row):
                continue  # skip blank rows
            # Skip footer/page-number rows: >50% empty and all non-empty cells numeric
            # OR >50% empty and single cell matches "Page N" / "N of M" pattern
            non_empty = [v for v in row if v]
            empty_ratio = (n_cols - len(non_empty)) / n_cols
            joined = ' '.join(non_empty)
            if empty_ratio >= 0.5 and (
                all(self._is_numeric(v) for v in non_empty)
                or _footer_re.match(joined)
            ):
                continue
            data_rows.append(row)

        if not data_rows:
            return None

        return pd.DataFrame(data_rows, columns=headers)

    # ── Shared utilities ──────────────────────────────────────────────────────

    def _table_to_df_headerless(self, table, headers):
        """
        Build a DataFrame from a pdfplumber table that contains ONLY data rows
        (no column-header row), using the supplied ``headers`` list.

        Used when a PDF has column names on page 1 only, and all remaining pages
        are pure data continuation (no repeated header row).

        Returns None if the table's actual column count doesn't match
        len(headers) — this prevents accidentally mapping a new table
        with different columns to the previous page's headers.
        """
        import re
        if not table or not headers:
            return None
        n_cols = len(headers)

        # Infer the table's real column count from non-blank rows.
        # If it doesn't match our headers, this is not a continuation page.
        data_widths = [
            sum(1 for cell in row if cell is not None and str(cell).strip())
            for row in table
        ]
        data_widths = [w for w in data_widths if w > 0]
        if not data_widths:
            return None
        table_col_count = max(data_widths)
        if table_col_count != n_cols:
            return None   # different column count → not a continuation page

        _footer_re = re.compile(
            r'^\s*(page\s*\d+(\s+of\s+\d+)?|\d+\s*/\s*\d+|\d+)\s*$', re.I
        )
        rows = []
        for row in table:
            cleaned = [str(cell).strip() if cell is not None else '' for cell in row]
            if not any(cleaned):           # skip fully blank rows
                continue
            non_empty = [v for v in cleaned if v]
            joined = ' '.join(non_empty)
            # Skip lone page-number footers
            if len(non_empty) == 1 and _footer_re.match(joined):
                continue
            # Pad / truncate to column count (handles rare minor misalignments)
            if len(cleaned) < n_cols:
                cleaned += [''] * (n_cols - len(cleaned))
            else:
                cleaned = cleaned[:n_cols]
            rows.append(cleaned)
        if not rows:
            return None
        return pd.DataFrame(rows, columns=headers)

    def _table_to_df(self, table):
        """
        Convert a pdfplumber raw table (list-of-lists) to a DataFrame.

        pdfplumber's text-strategy sometimes skips the header row when a PDF
        has a title line above the column names, causing the first data row
        (all numbers) to be used as the header.  We scan for the first row
        that contains at least one non-numeric, non-empty cell and treat that
        as the real header; any rows before it are discarded as title/preamble.
        """
        if not table or len(table) < 2:
            return None

        # ── Find the real header row ──────────────────────────────────────────
        header_row_idx = None
        for idx, row in enumerate(table):
            cells = [str(c).strip() for c in row if c is not None]
            non_empty = [c for c in cells if c]
            if not non_empty:
                continue  # blank row – skip
            # A header row must have at least one non-numeric cell
            if any(not self._is_numeric(c) for c in non_empty):
                header_row_idx = idx
                break

        if header_row_idx is None:
            return None   # every row is numeric – cannot identify a header

        raw_headers = table[header_row_idx]
        headers = []
        seen: dict = {}
        for i, h in enumerate(raw_headers):
            name = str(h).strip() if h is not None else ''
            if not name:
                name = f'col_{i}'
            # Deduplicate in case pdfplumber produces duplicate column names
            if name in seen:
                seen[name] += 1
                name = f'{name}_{seen[name]}'
            else:
                seen[name] = 0
            headers.append(name)

        rows = []
        for row in table[header_row_idx + 1:]:
            cleaned = [str(cell).strip() if cell is not None else '' for cell in row]
            if not any(cleaned):      # skip fully blank rows
                continue
            rows.append(cleaned)

        if not rows:
            return None
        return pd.DataFrame(rows, columns=headers)

    def _finalize(self, frames):
        """
        Merge per-page DataFrames into one, handling two common PDF layouts:

          • Vertical split   – pages continue the SAME columns with more rows
                               (e.g. rows 1-25 on page 1, rows 26-50 on page 2)
                               → pd.concat vertically

          • Horizontal split – an online converter couldn't fit all columns on one
                               page width, so it put col A-E on page 1 and col F-J
                               on page 2 with the SAME rows repeated.
                               → pd.concat horizontally (axis=1)

        Detection rule: two frames are "horizontally splittable" when they share
        the same number of data rows AND have NO overlapping column names.
        We greedily chain such frames into horizontal groups, then stack any
        remaining groups vertically.
        """
        if not frames:
            return pd.DataFrame()
        if len(frames) == 1:
            merged = frames[0].copy()
            for col in merged.columns:
                merged[col] = pd.to_numeric(merged[col], errors='ignore')
            return merged

        # ── Greedy grouping: build horizontal clusters ────────────────────────
        used = [False] * len(frames)
        groups = []   # each group is a list of frame indices to merge horizontally

        for i in range(len(frames)):
            if used[i]:
                continue
            group = [i]
            used[i] = True
            group_cols = set(frames[i].columns)
            group_rows = len(frames[i])

            for j in range(i + 1, len(frames)):
                if used[j]:
                    continue
                j_cols = set(frames[j].columns)
                j_rows = len(frames[j])
                # Merge horizontally if: same row count AND no shared column names
                if j_rows == group_rows and not (group_cols & j_cols):
                    group.append(j)
                    used[j] = True
                    group_cols |= j_cols

            groups.append(group)

        # ── Build one DataFrame per group (horizontal merge within group) ──────
        group_dfs = []
        for group in groups:
            if len(group) == 1:
                group_dfs.append(frames[group[0]])
            else:
                # Sort group frames left-to-right by their first column's name
                # so the original column order is preserved
                sorted_group = sorted(group, key=lambda idx: list(frames[idx].columns)[0])
                h_merged = pd.concat(
                    [frames[idx].reset_index(drop=True) for idx in sorted_group],
                    axis=1
                )
                group_dfs.append(h_merged)

        # ── Stack groups vertically (normal row continuation) ─────────────────
        merged = pd.concat(group_dfs, ignore_index=True)

        # Coerce numerics
        for col in merged.columns:
            merged[col] = pd.to_numeric(merged[col], errors='ignore')
        return merged

    @staticmethod
    def _is_numeric(s):
        try:
            float(s.replace(',', ''))
            return True
        except ValueError:
            return False

    def create_dataset(self, file_path, name, description, user_id=None):
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # Read file (CSV or PDF) and infer schema
            df = self._read_file_as_dataframe(file_path)
            schema = self._infer_schema(df)

            # Extract just the base filename (not full path)
            base_filename = os.path.basename(file_path)

            # Create dataset metadata with user_id
            dataset = Dataset(name, description, base_filename, schema, user_id)
            dataset_dict = dataset.to_dict()

            # Save dataset metadata
            if isinstance(self.db, dict):
                # Handle fallback dictionary case
                if "datasets" not in self.db:
                    self.db["datasets"] = []
                self.db["datasets"].append(dataset_dict)

                # Save data to a JSON file as fallback
                fallback_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'fallback_data')
                os.makedirs(fallback_dir, exist_ok=True)

                records = df.to_dict('records')
                with open(os.path.join(fallback_dir, f'data_{dataset.id}.json'), 'w') as f:
                    json.dump(records, f)
            else:
                # Normal MongoDB case
                self.db.datasets.insert_one(dataset_dict)

                # Save dataset contents
                collection_name = f'data_{dataset.id}'
                records = df.to_dict('records')
                if records:
                    self.db[collection_name].insert_many(records)

            return dataset
        except pd.errors.EmptyDataError:
            raise ValueError("The CSV file is empty")
        except pd.errors.ParserError:
            raise ValueError("Error parsing CSV file - check the format")
        except Exception as e:
            raise Exception(f"Failed to create dataset: {str(e)}")
        
    def delete_dataset(self, dataset_id, user_id):
        try:
            if isinstance(self.db, dict):
                # Handle fallback dictionary case
                datasets = self.db.get("datasets", [])
                dataset = next((d for d in datasets if d.get('id') == dataset_id), None)
                
                if not dataset:
                    return False
                    
                # Verify ownership
                if dataset.get('user_id') != user_id:
                    return False
                    
                # Remove from list
                self.db["datasets"] = [d for d in datasets if d.get('id') != dataset_id]
                
                # Delete fallback data file
                fallback_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'fallback_data')
                data_file = os.path.join(fallback_dir, f'data_{dataset_id}.json')
                if os.path.exists(data_file):
                    os.remove(data_file)
                    
                # Delete uploaded file if it exists
                if dataset.get('file_path') and os.path.exists(dataset['file_path']):
                    os.remove(dataset['file_path'])
                    
                return True
            else:
                # Normal MongoDB case
                dataset = self.db.datasets.find_one({'id': dataset_id})
                
                if not dataset:
                    return False
                    
                # Verify ownership
                if dataset.get('user_id') != user_id:
                    return False
                    
                # Delete dataset metadata
                self.db.datasets.delete_one({'id': dataset_id})
                
                # Delete dataset contents collection
                collection_name = f'data_{dataset_id}'
                self.db[collection_name].drop()
                
                # Delete uploaded file if it exists
                if dataset.get('file_path') and os.path.exists(dataset['file_path']):
                    os.remove(dataset['file_path'])
                    
                return True
        except Exception as e:
            print(f"Error deleting dataset: {str(e)}")
            return False
    
    def _infer_schema(self, df):
        schema = {}
        for column in df.columns:
            if pd.api.types.is_numeric_dtype(df[column]):
                schema[column] = 'number'
            elif pd.api.types.is_bool_dtype(df[column]):
                schema[column] = 'boolean'
            else:
                schema[column] = 'string'
        return schema