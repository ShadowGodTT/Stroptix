from __future__ import annotations

import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import pandas as pd

from .config import load_config
from .generator import GenerationContext, pick_top_per_member
from .io_excel import read_input, write_output, OUTPUT_SHEET_NAME
from .library import load_library


class StrOptixGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("StrOptix Lite - GUI (Temporary)")
        self.root.geometry("900x600")

        # Paths
        self.input_path = tk.StringVar(value=str(Path("data") / "sample_input.xlsx"))
        self.library_path = tk.StringVar(value=str(Path("data") / "plate_library.xlsx"))
        self.config_path = tk.StringVar(value=str(Path("data") / "config.yaml"))
        self.output_path = tk.StringVar(value=str(Path("results") / "output.xlsx"))

        self._build_form()
        self._build_table()
        self._build_status()

    def _build_form(self) -> None:
        frm = ttk.LabelFrame(self.root, text="Paths")
        frm.pack(fill=tk.X, padx=10, pady=10)

        def add_row(row: int, label: str, var: tk.StringVar, is_file: bool = True) -> None:
            ttk.Label(frm, text=label, width=20).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
            entry = ttk.Entry(frm, textvariable=var)
            entry.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=5)
            frm.columnconfigure(1, weight=1)

            def browse():
                if label.startswith("Output"):
                    # choose save-as path
                    initial = Path(var.get()) if var.get() else Path.cwd()
                    f = filedialog.asksaveasfilename(
                        parent=self.root,
                        title="Select output Excel",
                        defaultextension=".xlsx",
                        initialdir=str(initial.parent),
                        initialfile=initial.name,
                        filetypes=[("Excel", "*.xlsx")],
                    )
                else:
                    f = filedialog.askopenfilename(
                        parent=self.root,
                        title=f"Select {label}",
                        filetypes=[("All", "*.*"), ("Excel", "*.xlsx"), ("YAML", "*.yaml;*.yml")],
                    )
                if f:
                    var.set(f)

            ttk.Button(frm, text="Browse", command=browse).grid(row=row, column=2, padx=5, pady=5)

        add_row(0, "Input Excel", self.input_path)
        add_row(1, "Plate library", self.library_path)
        add_row(2, "Config YAML", self.config_path)
        add_row(3, "Output Excel", self.output_path)

        btns = ttk.Frame(frm)
        btns.grid(row=4, column=0, columnspan=3, sticky=tk.E, pady=(10, 0))
        ttk.Button(btns, text="Run", command=self._on_run).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btns, text="Preview Output", command=self._on_preview).pack(side=tk.RIGHT, padx=5)

    def _build_table(self) -> None:
        table_frame = ttk.LabelFrame(self.root, text="Preview (first 50 rows)")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(table_frame, show="headings")
        self.tree.pack(fill=tk.BOTH, expand=True)

        yscroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=yscroll.set)

    def _build_status(self) -> None:
        self.status = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status, anchor=tk.W)
        status_bar.pack(fill=tk.X, padx=10, pady=(0, 10))

    def _set_status(self, text: str) -> None:
        self.status.set(text)
        self.root.update_idletasks()

    def _run_pipeline(self) -> pd.DataFrame | None:
        try:
            inp = read_input(self.input_path.get())
            cfg = load_config(self.config_path.get())
            lib = load_library(self.library_path.get())

            ctx = GenerationContext(input=inp, config=cfg, library=lib)
            members = pick_top_per_member(ctx, inp.members_count)
            write_output(self.output_path.get(), members)

            # Build DataFrame similar to writer for preview
            data = [
                {
                    "Member id": m.member_id,
                    "Web start depth": m.web_start_depth_mm,
                    "Web end depth": m.web_end_depth_mm,
                    "Web thickness": m.web_thickness_mm,
                    "Inside flange width": m.if_width_mm,
                    "Inside flange thickness": m.if_thickness_mm,
                    "Outside flange width": m.of_width_mm,
                    "Outside flange thickness": m.of_thickness_mm,
                    "Weight (kg/m)": round(m.weight_kg_per_m, 3),
                    "Status": m.status,
                }
                for m in members
            ]
            return pd.DataFrame(data)
        except Exception as e:  # pylint: disable=broad-except
            messagebox.showerror("Error", f"Failed to run: {e}")
            return None

    def _on_run(self) -> None:
        def task():
            self._set_status("Running...")
            df = self._run_pipeline()
            if df is not None:
                self._set_status(f"Done. Wrote {self.output_path.get()} ({len(df)} rows)")
                self._populate_tree(df)
            else:
                self._set_status("Failed")

        threading.Thread(target=task, daemon=True).start()

    def _on_preview(self) -> None:
        out = Path(self.output_path.get())
        if not out.exists():
            messagebox.showinfo("Preview", "Output not found. Run first to generate.")
            return
        try:
            xl = pd.ExcelFile(out)
            df = pd.read_excel(xl, sheet_name=OUTPUT_SHEET_NAME)
            self._populate_tree(df)
            self._set_status(f"Preview loaded from {out}")
        except Exception as e:  # pylint: disable=broad-except
            messagebox.showerror("Error", f"Failed to preview: {e}")

    def _populate_tree(self, df: pd.DataFrame) -> None:
        # Clear existing
        for col in self.tree.get_children(""):
            self.tree.delete(col)
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = list(df.columns)
        for c in df.columns:
            self.tree.heading(c, text=str(c))
            self.tree.column(c, width=140, anchor=tk.CENTER)

        for _, row in df.head(50).iterrows():
            values = [row[c] for c in df.columns]
            self.tree.insert("", tk.END, values=values)


def main() -> None:  # pragma: no cover
    root = tk.Tk()
    app = StrOptixGUI(root)
    root.mainloop()


if __name__ == "__main__":  # pragma: no cover
    main()
