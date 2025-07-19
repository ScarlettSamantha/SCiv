#!/usr/bin/env python3
import concurrent.futures
import datetime
import gzip
import re
import signal
import sys
import threading
import tkinter as tk
from argparse import ArgumentParser, Namespace
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict, List, Set, Tuple, Union

from ttkthemes import ThemedTk

COLOR_MAP: Dict[str, str] = {
    "int": "#b58900",
    "float": "#2aa198",
    "bool": "#d33682",
    "str": "#859900",
    "NoneType": "#657b83",
    "dict": "#dc322f",
    "list": "#dc322f",
    "tuple": "#dc322f",
    "set": "#dc322f",
}

ROW_BG: Dict[str, str] = {k: v.replace("dc322f", "ffd6d6") for k, v in COLOR_MAP.items()}


class EditValueDialog(tk.Toplevel):
    def __init__(self, master: tk.Tk, current_type: str, current_val: str) -> None:
        super().__init__(master)
        self.withdraw()
        self.transient(master)
        self.title("Edit Value")

        self.result: Tuple[str, Any] = (current_type, current_val)

        ttk.Label(self, text="Type:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.type_var = tk.StringVar(value=current_type)

        type_cb = ttk.Combobox(
            self,
            textvariable=self.type_var,
            values=["int", "float", "bool", "str", "NoneType"],
            state="readonly",
        )
        type_cb.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        type_cb.bind("<<ComboboxSelected>>", lambda e: self._render_value_field())

        self.value_frame = ttk.Frame(self)
        self.value_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="OK", command=self._on_ok).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left")

        self._render_value_field(current_val)

        self.deiconify()
        self.wait_visibility()
        self.grab_set()
        self.focus_force()

    def _render_value_field(self, initial: str = "") -> None:
        for w in self.value_frame.winfo_children():
            w.destroy()

        t = self.type_var.get()
        ttk.Label(self.value_frame, text="Value:").grid(row=0, column=0, sticky="w")
        if t == "bool":
            self.val_var = tk.StringVar(value=str(initial))
            cb = ttk.Combobox(self.value_frame, textvariable=self.val_var, values=["True", "False"], state="readonly")
            cb.grid(row=0, column=1, sticky="ew")

        elif t == "NoneType":
            self.val_var = tk.StringVar(value="null")
            lbl = ttk.Label(self.value_frame, text="null")
            lbl.grid(row=0, column=1, sticky="w")
        else:
            self.val_var = tk.StringVar(value=initial)
            entry = ttk.Entry(self.value_frame, textvariable=self.val_var)
            entry.grid(row=0, column=1, sticky="ew")

            if t in ("int", "float"):

                def validate(s: str) -> bool:
                    if s == "":
                        return True
                    try:
                        int(s) if t == "int" else float(s)
                        return True
                    except ValueError:
                        return False

                vcmd = (self.register(lambda s: validate(s)), "%P")  #   type: ignore
                entry.configure(validate="key", validatecommand=vcmd)

        self.value_frame.columnconfigure(1, weight=1)

    def _on_ok(self) -> None:
        t = self.type_var.get()
        raw = self.val_var.get().strip().replace("'", "").replace('"', "")

        if t == "int":
            val = int(raw)
        elif t == "float":
            val = float(raw)
        elif t == "bool":
            val = raw == "True"
        elif t == "NoneType":
            val = None
        else:
            val = raw

        self.result = (t, val)
        self.destroy()


def load_json(path: str) -> Any:
    try:
        import ujson as json_module
    except ImportError:
        import json as json_module
    if path.endswith(".gz"):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json_module.load(f)
    with open(path, "r", encoding="utf-8") as f:
        return json_module.load(f)


def prepare_items(obj: Any) -> List[Tuple[Union[str, int], str, str, bool]]:
    items: List[Tuple[Union[str, int], str, str, bool]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():  # type: ignore
            displayed = repr(v) if not isinstance(v, str) else v  # type: ignore
            items.append((k, type(v).__name__, displayed, isinstance(v, (dict, list, tuple, set))))  # type: ignore
    elif isinstance(obj, (list, tuple, set)):
        for i, v in enumerate(obj):  # type: ignore
            items.append((i, type(v).__name__, repr(v), isinstance(v, (dict, list, tuple, set))))  # type: ignore
    return items


class JsonInspector(ThemedTk):
    def __init__(self, path: str) -> None:
        super().__init__(theme="radiance")
        signal.signal(signalnum=signal.SIGINT, handler=lambda _s, _f: self.destroy())
        self.bind_all(sequence="<Control-c>", func=lambda e: self.destroy())
        self.title(string=f"Json Inspector <{path}>")
        self.geometry(newGeometry="1400x900")

        self._search_results: List[str] = []
        self._search_idx: int = -1

        self.loading = True
        self._dots = 0
        self.loading_label = ttk.Label(self, text="Loading", font=("TkDefaultFont", 16))
        self.loading_label.place(relx=0.5, rely=0.5, anchor="center")
        self.breadcrumb_label: ttk.Label = ttk.Label(self, text="", font=("TkDefaultFont", 11))
        self.breadcrumb_label.pack(fill=tk.X, padx=5, pady=(4, 0))
        self._animate()

        self._executor = concurrent.futures.ProcessPoolExecutor()
        self.data: Any = None
        self._expanded: Set[str] = set()

        self._build_ui()

        threading.Thread(target=self._load_data, args=(path,), daemon=True).start()
        self._current_path: str = path
        self.last_save_time: datetime.datetime | None = None

    def _get_path_keys(self, iid: str) -> List[str]:
        path: List[str] = []
        node = iid
        while node:
            text: str = self.tree.item(item=node, option="text")
            path.insert(0, text)
            node: str = self.tree.parent(item=node)
        return [path[0].split(":")[0]] + path[1:]

    def _update_breadcrumbs(self, iid: str) -> None:
        keys: List[str] = self._get_path_keys(iid)
        crumb: str = " > ".join(keys)
        self.breadcrumb_label.config(text=crumb)

    def _on_search(self) -> None:
        q: str = self.search_var.get().strip()
        if not q:
            return

        pat: re.Pattern[str] = re.compile(pattern=re.escape(pattern=q), flags=re.IGNORECASE)
        self._search_results = self._find_matches(obj=self.data, path=[], pat=pat)  # type: ignore
        if not self._search_results:
            messagebox.showinfo("Search", f"No matches for {q!r}")  # type: ignore
            return

        self._search_idx = 0
        self._goto_search_result()

    def _find_matches(self, obj: Any, path: List[Union[str, int]], pat: re.Pattern[Any]) -> List[List[Union[str, int]]]:
        results: List[List[Union[str, int]]] = []

        if isinstance(obj, dict):
            for k, v in obj.items():  # type: ignore
                if pat.search(str(k)):  # type: ignore
                    results.append(path + [k])  # type: ignore
                if not isinstance(v, (dict, list, tuple, set)) and pat.search(str(v)):  # type: ignore
                    results.append(path + [k])
                results += self._find_matches(v, path + [k], pat)

        elif isinstance(obj, (list, tuple, set)):
            for idx, v in enumerate(obj):  # type: ignore
                if not isinstance(v, (dict, list, tuple, set)) and pat.search(str(v)):  # type: ignore
                    results.append(path + [idx])
                results += self._find_matches(v, path + [idx], pat)

        return results

    def _goto_search_result(self) -> None:
        path: str = self._search_results[self._search_idx]
        root_iid: str = next(iter(self.tree.get_children("")))
        self._expand_and_select(root_iid, [path])

    def _expand_and_select(
        self,
        iid: str,
        path: List[Union[str, int]],
    ) -> None:
        if not path:
            self.tree.see(iid)
            self.tree.selection_set(iid)
            self.tree.focus(iid)
            return

        if iid not in self._expanded:
            self.tree.item(iid, open=True)
            self._on_open(None)
        key = str(path[0])
        for child in self.tree.get_children(iid):
            if self.tree.item(child, "text") == key:
                return self._expand_and_select(child, path[1:])

    def _on_next(self) -> None:
        if not self._search_results:
            return
        self._search_idx = (self._search_idx + 1) % len(self._search_results)
        self._goto_search_result()

    def _on_prev(self) -> None:
        if not self._search_results:
            return
        self._search_idx = (self._search_idx - 1) % len(self._search_results)
        self._goto_search_result()

    def _build_search_ui(self) -> None:
        frm = ttk.Frame(self)
        frm.pack(fill=tk.X, padx=5, pady=(0, 5))

        self.search_var = tk.StringVar()
        ttk.Label(frm, text="Search:").pack(side="left")
        entry = ttk.Entry(frm, textvariable=self.search_var)
        entry.pack(side="left", fill=tk.X, expand=True, padx=(2, 5))
        entry.bind("<Return>", lambda e: self._on_search())

        ttk.Button(frm, text="Search", command=self._on_search).pack(side="left", padx=2)
        ttk.Button(frm, text="◀ Prev", command=self._on_prev).pack(side="left", padx=2)
        ttk.Button(frm, text="Next ▶", command=self._on_next).pack(side="left", padx=2)

    def _build_ui(self) -> None:
        menubar = tk.Menu(self)

        filemenu = tk.Menu(menubar, tearoff=0)

        filemenu.add_command(label="Open...", command=self._open_file, accelerator="Ctrl+O")
        self.bind_all("<Control-o>", lambda e: self._open_file())

        filemenu.add_command(label="Save", command=self._save_file, accelerator="Ctrl+S")
        self.bind_all("<Control-s>", lambda e: self._save_file())

        filemenu.add_command(label="Save As…", command=self._save_as_file, accelerator="Ctrl+Shift+S")
        self.bind_all("<Control-Shift-s>", lambda e: self._save_as_file())

        filemenu.add_separator()

        filemenu.add_command(label="Quit", command=self.destroy, accelerator="Ctrl+Q")
        self.bind_all("<Control-q>", lambda e: self.destroy())

        menubar.add_cascade(label="File", menu=filemenu)
        self._filemenu: tk.Menu = filemenu

        view = tk.Menu(menubar, tearoff=0)
        self.show_vals = tk.BooleanVar(self, value=False)
        view.add_checkbutton(label="Show Values", variable=self.show_vals, command=self._toggle)
        menubar.add_cascade(label="View", menu=view)

        self._build_search_ui()

        self.status_label = ttk.Label(menubar, text="Loading", foreground="red", font=("TkDefaultFont", 10))
        self.status_label.pack(side=tk.RIGHT, padx=5, pady=2)

        self.config(menu=menubar)  # type: ignore

        self.pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.pane.pack(fill=tk.BOTH, expand=True)

        self.prop_frame = ttk.Frame(self.pane)
        self.prop_tree = ttk.Treeview(self.prop_frame, columns=("key", "type", "value"), show="headings")
        for col, title in [("key", "Key"), ("type", "Type"), ("value", "Value")]:
            self.prop_tree.heading(col, text=title)
            self.prop_tree.column(col, stretch=True)

        prop_vsb = ttk.Scrollbar(self.prop_frame, orient=tk.VERTICAL, command=self.prop_tree.yview)  # type: ignore
        self.prop_tree.configure(yscrollcommand=prop_vsb.set)
        self.prop_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.prop_tree.bind("<Double-1>", self._on_prop_double_click)

        prop_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.pane.add(self.prop_frame, weight=1)  # type: ignore

        self.tree_frame = ttk.Frame(self.pane)
        self.tree = ttk.Treeview(self.tree_frame, columns=("type"), show="tree headings", selectmode="browse")

        self.tree.heading("#0", text="Key")
        self.tree.heading("type", text="Type")
        self.tree.column("type", width=80)

        tree_vsb = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)  # type: ignore

        self.tree.configure(yscrollcommand=tree_vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.pane.add(self.tree_frame, weight=3)  # type: ignore

        self._row_count = 0
        self.tree.tag_configure("odd", background="#f9f9f9")
        self.tree.tag_configure("even", background="#e0e0e0")

        self.tree.bind("<<TreeviewOpen>>", self._on_open)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        year = datetime.datetime.now().year
        self.footer = ttk.Frame(self)
        self.footer.pack(side=tk.BOTTOM, fill=tk.X)

        self.loaded_file_label = ttk.Label(master=self.footer, text="", font=("TkDefaultFont", 10))
        self.loaded_file_label.pack(side=tk.LEFT, padx=5, pady=2)

        self.save_time_label = ttk.Label(master=self.footer, text="", font=("TkDefaultFont", 10))
        self.save_time_label.pack(side=tk.LEFT, padx=5, pady=2)

        self.copy_label = ttk.Label(
            master=self.footer,
            text=f"© Scarlett Verheul <scarlett.verheul@gmail.com> {year}",
            font=("TkDefaultFont", 10),
        )
        self.copy_label.pack(side=tk.LEFT, padx=5, pady=2)

        self.footer_status = ttk.Label(self.footer, text="Loading…", foreground="red", font=("TkDefaultFont", 10))
        self.footer_status.pack(side=tk.RIGHT, padx=5, pady=2)

        self.after(60_000, self._update_save_time)

    def _on_prop_double_click(self, event: tk.Event[Any]) -> None:
        item: str = self.prop_tree.identify_row(event.y)
        if not item:
            return

        cur_type = self.prop_tree.set(item, "type")
        if cur_type in ("dict", "list", "tuple", "set"):
            return

        cur_val = self.prop_tree.set(item, "value") if "value" in self.prop_tree["columns"] else ""
        dlg = EditValueDialog(self, cur_type, cur_val)
        self.wait_window(dlg)
        new_type, new_val = dlg.result

        self.prop_tree.set(item, "type", new_type)
        if "value" in self.prop_tree["columns"]:
            text = repr(new_val) if not isinstance(new_val, str) else new_val
            self.prop_tree.set(item, "value", text)

        parent_obj = self._get_obj(self._current_obj_iid)
        raw_key = self.prop_tree.set(item, "key")
        key: Union[int, str] = int(raw_key) if isinstance(parent_obj, list) else raw_key

        if isinstance(parent_obj, dict):
            parent_obj[key] = new_val
        elif isinstance(parent_obj, list):
            parent_obj[key] = new_val  # type: ignore
        else:
            messagebox.showerror(title="Edit Error", message="Cannot assign to a non-container value.")  # type: ignore
            return

    def _open_file(self) -> None:
        path: str = filedialog.askopenfilename(title="Open JSON", filetypes=[("JSON files", ".json .json.gz")])
        if not path:
            return
        self.loading = True
        self.status_label.config(text="Loading", foreground="red")
        self.footer_status.config(text="Loading…", foreground="red")
        self.loading_label = ttk.Label(self, text="Loading", font=("TkDefaultFont", 16))
        self.loading_label.place(relx=0.5, rely=0.5, anchor="center")
        self._expanded.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for item in self.prop_tree.get_children():
            self.prop_tree.delete(item)
        threading.Thread(target=self._load_data, args=(path,), daemon=True).start()

        self.title(string=f"Json Inspector <{path}>")

    def _animate(self) -> None:
        if not self.loading:
            return

        self.loading_label.config(text="Loading" + "." * self._dots)
        self._dots = (self._dots + 1) % 4
        self.after(500, self._animate)

    def _load_data(self, path: str) -> None:
        self.data = load_json(path)
        self.after(0, self._init_tree)

    def _init_tree(self) -> None:
        self.loading = False

        self._filemenu.entryconfig(index="Save", state="normal")
        self._filemenu.entryconfig(index="Save As…", state="normal")

        self.status_label.config(text="Loaded", foreground="green")
        self.footer_status.config(text="Loaded", foreground="green")
        self.loading_label.destroy()

        root_text = f"root: ({type(self.data).__name__})"
        root_id = self.tree.insert("", "end", text=root_text, values=(type(self.data).__name__, ""), open=False)
        self.tree.insert(root_id, "end", text="(loading…)")

    def _save_file(self) -> None:
        self._write_json(path=self._current_path)
        self._record_save()

    def _save_as_file(self) -> None:
        new_path = filedialog.asksaveasfilename(
            title="Save JSON As",
            defaultextension=".json",
            filetypes=[("JSON files", ".json .gz"), ("All files", "*.*")],
        )
        if not new_path:
            return
        self._current_path = new_path
        self._write_json(new_path)
        self.loaded_file_label.config(text=f"File: {self._current_path}")
        self._record_save()

    def _write_json(self, path: str) -> None:
        try:
            import ujson as json_module
        except ImportError:
            import json as json_module

        mode, opener = ("wt", open)
        if path.endswith(".gz"):
            import gzip

            mode, opener = ("wt", gzip.open)

        with opener(path, mode, encoding="utf-8") as f:
            json_module.dump(self.data, f, indent=4)

        self.status_label.config(text=f"Saved: {path}", foreground="blue")
        self.footer_status.config(text="Saved", foreground="blue")

    def _on_open(self, _: Any) -> None:
        iid: str = self.tree.focus()
        if iid in self._expanded:
            return

        self._expanded.add(iid)
        for c in self.tree.get_children(iid):
            if self.tree.item(c, "text") == "(loading…)":
                self.tree.delete(c)

        obj = self._get_obj(iid)
        future: concurrent.futures.Future[List[Tuple[Union[str, int], str, str, bool]]] = self._executor.submit(
            prepare_items, obj
        )
        future.add_done_callback(lambda f, iid=iid: self.after(0, lambda: self._start_chunk(iid, f.result())))

    def _start_chunk(self, iid: str, items: List[Tuple[Any, str, str, bool]]) -> None:
        self._chunk_queue = [(iid, k, typ, val, is_cont) for k, typ, val, is_cont in items]
        self._process_chunk()

    def _process_chunk(self) -> None:
        batch = 100
        for _ in range(min(batch, len(self._chunk_queue))):
            parent, key, typ, val, is_cont = self._chunk_queue.pop(0)
            node_id: str = self.tree.insert(
                parent=parent,
                index="end",
                text=str(key),
                values=(typ, val),
                tags=("odd",) if self._row_count % 2 else ("even",),
            )
            self._row_count += 1

            color: str | None = COLOR_MAP.get(typ)
            bg: str | None = ROW_BG.get(typ)

            if color or bg:
                tag: str = f"t_{typ}"
                if not self.tree.tag_has(tagname=tag):
                    self.tree.tag_configure(tagname=tag, foreground=color or "", background=bg or "")
                tags: List[str] = list(self.tree.item(item=node_id, option="tags"))
                tags.append(tag)
                self.tree.item(item=node_id, tags=tuple(tags))

            if is_cont:
                self.tree.insert(parent=node_id, index="end", text="(loading…)")

        if self._chunk_queue:
            self.after(10, self._process_chunk)

    def _get_obj(self, iid: str) -> Any:
        path: List[str] = []
        node: str = iid

        while node:
            text: str = self.tree.item(node, "text")
            path.append(text)
            node = self.tree.parent(node)

        path = path[::-1][1:]
        o = self.data
        for key in path:
            if isinstance(o, (list, tuple)):
                try:
                    index = int(key)
                except ValueError:
                    raise KeyError(f"Invalid list index: {key}")
                o = o[index]  # type: ignore
            else:
                o = o[key]  # type: ignore
        return o  # type: ignore

    def _toggle(self) -> None:
        cols = ("type", "value") if self.show_vals.get() else ("type",)
        self.tree.configure(displaycolumns=cols)

    def _on_select(self, _: Any) -> None:
        iid: str = self.tree.focus()
        self._current_obj_iid = iid
        self._update_breadcrumbs(iid)
        obj = self._get_obj(iid)
        for row in self.prop_tree.get_children():
            self.prop_tree.delete(row)
        if isinstance(obj, dict):
            for k, v in obj.items():  # type: ignore
                typ: str = type(v).__name__  # type: ignore
                val: str = (
                    "[expand]" if isinstance(v, (dict, list, tuple, set)) else v if isinstance(v, str) else repr(v)  # type: ignore
                )  # type: ignore
                self.prop_tree.insert(parent="", index="end", values=(k, typ, val))  # type: ignore
        elif isinstance(obj, (list, tuple, set)):
            for i, v in enumerate(obj):  # type: ignore
                typ = type(v).__name__  # type: ignore
                val = "[expand]" if isinstance(v, (dict, list, tuple, set)) else v if isinstance(v, str) else repr(v)  # type: ignore
                self.prop_tree.insert(parent="", index="end", values=(i, typ, val))
        else:
            typ = type(obj).__name__
            val = obj if isinstance(obj, str) else repr(obj)
            self.prop_tree.insert(parent="", index="end", values=("Value", typ, val))

    def _record_save(self) -> None:
        self.last_save_time = datetime.datetime.now()
        self._update_save_time(immediate=True)

    def _update_save_time(self, immediate: bool = False) -> None:
        if self.last_save_time:
            delta: datetime.timedelta = datetime.datetime.now() - self.last_save_time
            mins = int(delta.total_seconds() // 60)
            if mins == 0:
                text = "Last saved: just now"
            else:
                text = f"Last saved: {mins} min ago"
            self.save_time_label.config(text=text)
        if not immediate:
            self.after(60_000, self._update_save_time)


if __name__ == "__main__":
    parser = ArgumentParser(description="Inspect JSON file with GUI")
    parser.add_argument("path", nargs="?")
    a: Namespace = parser.parse_args()
    if not a.path:
        a.path = filedialog.askopenfilename(title="Open JSON", filetypes=[("JSON files", ".json .json.gz")])
        if not a.path:
            sys.exit(0)
    try:
        JsonInspector(a.path).mainloop()
    except KeyboardInterrupt:
        sys.exit(0)
