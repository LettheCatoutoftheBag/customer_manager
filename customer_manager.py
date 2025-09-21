# 引入所有需要的模組
import tkinter as tk  # GUI 程式庫 Tkinter 的主要模組
from tkinter import ttk, messagebox  # ttk 提供更現代的元件，messagebox 用於彈出提示視窗
import sqlite3  # Python 內建的 SQLite 資料庫模組
import os  # (在此專案中未使用，但保留著以備不時之需)

# --- 主應用程式類別 ---
class CustomerApp:
    """
    客戶管理應用程式的主類別。
    這個類別封裝了所有與應用程式相關的資料和功能，
    包括 UI 介面、資料庫操作和事件處理。
    """
    def __init__(self, root):
        """
        類別的初始化函式 (建構子)。
        當一個 CustomerApp 物件被建立時，這個函式會被自動呼叫。
        :param root: Tkinter 的主視窗 (Tk) 物件。
        """
        # --- 基礎設定 ---
        self.root = root  # 將主視窗物件儲存為實例變數
        self.root.title("簡易客戶分級系統")  # 設定視窗標題
        self.root.geometry("850x600")  # 設定視窗的初始大小

        # --- 實例變數 ---
        self.db_name = "database.db"  # 資料庫檔案名稱
        self.details_window = None  # 用來追蹤詳細資料視窗是否存在，避免重複開啟
        
        # --- 程式啟動流程 ---
        self.conn = self.init_database()  # 初始化資料庫，並取得連線物件
        self.create_widgets()  # 建立所有 UI 元件
        self.load_categories()  # 從資料庫載入分類資料
        self.load_customers()  # 從資料庫載入客戶資料

    def init_database(self):
        """
        初始化資料庫。如果資料庫檔案或資料表不存在，則會自動建立。
        :return: 返回一個資料庫連線物件。
        """
        conn = sqlite3.connect(self.db_name)  # 連線到 SQLite 資料庫檔案
        cursor = conn.cursor()  # 建立一個 cursor 物件，用來執行 SQL 指令

        # 建立「分類」資料表 (categories)
        # IF NOT EXISTS 可以確保如果資料表已存在，不會重複建立而報錯
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )""")
        
        # 建立「客戶」資料表 (customers)
        # FOREIGN KEY 設定了與 categories 資料表的關聯
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category_id INTEGER,
            notes TEXT,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )""")
        
        # 檢查分類表是否為空，如果是，則新增一些預設分類
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            default_categories = ["VIP 客戶", "活躍客戶", "潛在客戶", "新客戶"]
            for cat in default_categories:
                # 使用 ? 作為佔位符，可以防止 SQL 注入攻擊
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
        
        conn.commit()  # 提交變更，將上述操作寫入資料庫檔案
        return conn  # 返回連線物件

    def create_widgets(self):
        """
        負責建立應用程式中所有的使用者介面 (UI) 元件。
        """
        # --- 主框架，作為所有元件的容器 ---
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- 左側框架：包含新增客戶和分類管理 ---
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # --- 1. 新增客戶區塊 ---
        customer_frame = ttk.LabelFrame(left_frame, text="新增客戶", padding="10")
        customer_frame.pack(fill=tk.X, pady=(0, 10))
        # 使用 .grid() 進行精確的網格佈局
        ttk.Label(customer_frame, text="客戶 ID:").grid(row=0, column=0, sticky="w", pady=2)
        self.customer_id_entry = ttk.Entry(customer_frame, width=30)
        self.customer_id_entry.grid(row=0, column=1, sticky="ew", pady=2)
        # ... (其他新增客戶的元件)
        ttk.Label(customer_frame, text="客戶名稱:").grid(row=1, column=0, sticky="w", pady=2)
        self.customer_name_entry = ttk.Entry(customer_frame)
        self.customer_name_entry.grid(row=1, column=1, sticky="ew", pady=2)
        ttk.Label(customer_frame, text="分類:").grid(row=2, column=0, sticky="w", pady=2)
        self.category_combobox = ttk.Combobox(customer_frame, state="readonly")
        self.category_combobox.grid(row=2, column=1, sticky="ew", pady=2)
        ttk.Label(customer_frame, text="備註:").grid(row=3, column=0, sticky="w", pady=2)
        self.notes_entry = tk.Text(customer_frame, height=4, width=30)
        self.notes_entry.grid(row=3, column=1, sticky="ew", pady=2)
        add_customer_btn = ttk.Button(customer_frame, text="新增客戶", command=self.add_customer)
        add_customer_btn.grid(row=4, column=1, sticky="e", pady=10)

        # --- 2. 分類管理區塊 ---
        category_frame = ttk.LabelFrame(left_frame, text="分類管理", padding="10")
        category_frame.pack(fill=tk.X)
        ttk.Label(category_frame, text="新分類名稱:").grid(row=0, column=0, sticky="w", pady=2)
        self.new_category_entry = ttk.Entry(category_frame, width=30)
        self.new_category_entry.grid(row=0, column=1, sticky="ew", pady=2)
        btn_frame = ttk.Frame(category_frame)
        btn_frame.grid(row=1, column=1, sticky="e", pady=10)
        add_cat_btn = ttk.Button(btn_frame, text="新增", command=self.add_category)
        add_cat_btn.pack(side=tk.LEFT, padx=(0, 5))
        del_cat_btn = ttk.Button(btn_frame, text="刪除選定分類", command=self.delete_category)
        del_cat_btn.pack(side=tk.LEFT)

        # --- 右側框架：包含客戶列表和篩選功能 ---
        right_frame = ttk.LabelFrame(main_frame, text="客戶列表", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # --- 篩選功能區 ---
        filter_frame = ttk.Frame(right_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(filter_frame, text="依分類篩選:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_category_combobox = ttk.Combobox(filter_frame, state="readonly", width=20)
        self.filter_category_combobox.pack(side=tk.LEFT, padx=(0, 5))
        apply_filter_btn = ttk.Button(filter_frame, text="篩選", command=self.apply_filter)
        apply_filter_btn.pack(side=tk.LEFT, padx=(0, 5))
        clear_filter_btn = ttk.Button(filter_frame, text="顯示全部", command=self.clear_filter)
        clear_filter_btn.pack(side=tk.LEFT)

        # --- 客戶列表 (使用 Treeview 元件) ---
        columns = ("id", "name", "category", "notes")
        self.tree = ttk.Treeview(right_frame, columns=columns, show="headings")
        self.tree.heading("id", text="客戶 ID")
        self.tree.heading("name", text="客戶名稱")
        self.tree.heading("category", text="分類")
        self.tree.heading("notes", text="備註")
        self.tree.column("id", width=100)
        self.tree.column("name", width=120)
        self.tree.column("category", width=100)
        self.tree.column("notes", width=200)
        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(5,0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- 修改與刪除按鈕區 ---
        action_frame = ttk.Frame(right_frame)
        action_frame.pack(fill=tk.X, pady=(5, 0))
        edit_btn = ttk.Button(action_frame, text="修改選定客戶", command=self.open_details_window)
        edit_btn.pack(side=tk.LEFT, padx=(0, 5))
        delete_btn = ttk.Button(action_frame, text="刪除選定客戶", command=self.delete_customer)
        delete_btn.pack(side=tk.LEFT)

        # --- 設定右鍵選單 ---
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="修改選定客戶", command=self.open_details_window)
        self.context_menu.add_command(label="刪除選定客戶", command=self.delete_customer)

        # --- 綁定事件 ---
        self.tree.bind("<Button-3>", self.show_context_menu)  # 綁定滑鼠右鍵點擊事件
        self.tree.bind("<Double-1>", self.on_double_click)  # 綁定滑鼠左鍵雙擊事件

    # --- 事件處理函式 ---
    def on_double_click(self, event):
        """處理雙擊事件，以唯讀模式打開詳細資料視窗"""
        selection = self.tree.identify_row(event.y)
        if selection:
            self.tree.selection_set(selection) 
            self.open_details_window(mode='view')

    def show_context_menu(self, event):
        """在滑鼠點擊的位置顯示右鍵選單"""
        selection = self.tree.identify_row(event.y)
        if selection:
            self.tree.selection_set(selection)
            self.context_menu.post(event.x_root, event.y_root)
    
    # --- 核心邏輯函式 ---
    def open_details_window(self, mode='edit'):
        """
        打開詳細資料視窗。此函式被重構成可處理 'edit' 和 'view' 兩種模式。
        """
        # --- 防呆機制：檢查是否已有視窗開啟 ---
        if self.details_window and self.details_window.winfo_exists():
            self.details_window.lift()  # 如果視窗已存在，就把它帶到最前面
            return  # 然後結束函式，不再開啟新視窗

        selected_item = self.tree.selection()
        if not selected_item:
            if mode == 'edit':
                messagebox.showwarning("操作錯誤", "請先在列表中選擇一位客戶。")
            return

        customer_data = self.tree.item(selected_item, 'values')
        cust_id, name, category, notes = customer_data

        # 建立一個 Toplevel 視窗，它是一個獨立於主視窗的新視窗
        self.details_window = tk.Toplevel(self.root)
        is_readonly = (mode == 'view')
        window_title = "檢視客戶資料" if is_readonly else "修改客戶資料"
        self.details_window.title(window_title)

        frame = ttk.Frame(self.details_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # 根據模式設定元件的狀態 (可編輯或唯讀)
        # ... (此處省略重複的元件建立程式碼，邏輯與 create_widgets 相似)
        ttk.Label(frame, text="客戶 ID:").grid(row=0, column=0, sticky="w", pady=5)
        id_entry = ttk.Entry(frame, width=30); id_entry.insert(0, cust_id); id_entry.config(state='readonly')
        id_entry.grid(row=0, column=1, pady=5)
        ttk.Label(frame, text="客戶名稱:").grid(row=1, column=0, sticky="w", pady=5)
        name_entry = ttk.Entry(frame, width=30); name_entry.insert(0, name)
        if is_readonly: name_entry.config(state='readonly')
        name_entry.grid(row=1, column=1, pady=5)
        ttk.Label(frame, text="分類:").grid(row=2, column=0, sticky="w", pady=5)
        cat_combobox = ttk.Combobox(frame, state="readonly", values=list(self.categories.keys())); cat_combobox.set(category)
        if is_readonly: cat_combobox.config(state='disabled')
        cat_combobox.grid(row=2, column=1, sticky="ew", pady=5)
        ttk.Label(frame, text="備註:").grid(row=3, column=0, sticky="w", pady=5)
        notes_text = tk.Text(frame, height=5, width=30); notes_text.insert("1.0", notes)
        if is_readonly: notes_text.config(state='disabled')
        notes_text.grid(row=3, column=1, pady=5)
        
        if mode == 'edit':
            # 在 'edit' 模式下，顯示 "儲存變更" 按鈕
            save_btn = ttk.Button(frame, text="儲存變更", 
                                  command=lambda: self.save_customer_changes(
                                      self.details_window, cust_id, name_entry, cat_combobox, notes_text
                                  ))
            save_btn.grid(row=4, column=1, sticky="e", pady=10)
        else: # 'view' mode
            # 在 'view' 模式下，顯示 "關閉" 按鈕
            close_btn = ttk.Button(frame, text="關閉", command=self.details_window.destroy)
            close_btn.grid(row=4, column=1, sticky="e", pady=10)
            
    # --- 資料庫操作函式 ---
    def load_categories(self):
        """從資料庫載入所有分類，並更新 UI 上的下拉選單"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM categories ORDER BY name")
        # 使用字典推導式，建立一個 "分類名稱 -> 分類ID" 的對應字典
        self.categories = {name: cat_id for cat_id, name in cursor.fetchall()}
        category_names = list(self.categories.keys())
        self.category_combobox['values'] = category_names
        if category_names: self.category_combobox.current(0)
        filter_category_names = ["— 全部顯示 —"] + category_names
        self.filter_category_combobox['values'] = filter_category_names
        if filter_category_names: self.filter_category_combobox.current(0)
    
    def load_customers(self, category_id=None):
        """從資料庫載入客戶資料，並顯示在 Treeview 列表中。可選擇性地依分類 ID 篩選"""
        for item in self.tree.get_children(): self.tree.delete(item)
        cursor = self.conn.cursor()
        params = []
        query = "SELECT c.id, c.name, cat.name, c.notes FROM customers c LEFT JOIN categories cat ON c.category_id = cat.id"
        if category_id:
            query += " WHERE c.category_id = ?"
            params.append(category_id)
        query += " ORDER BY c.name"
        cursor.execute(query, params)
        for row in cursor.fetchall(): self.tree.insert("", tk.END, values=row)

    def apply_filter(self):
        """篩選按鈕的處理函式"""
        selected_category_name = self.filter_category_combobox.get()
        if selected_category_name == "— 全部顯示 —":
            self.load_customers()
        else:
            category_id = self.categories.get(selected_category_name)
            if category_id: self.load_customers(category_id=category_id)
                
    def clear_filter(self):
        """顯示全部按鈕的處理函式"""
        self.filter_category_combobox.current(0)
        self.load_customers()

    def add_customer(self):
        """新增客戶按鈕的處理函式"""
        cust_id = self.customer_id_entry.get().strip()
        name = self.customer_name_entry.get().strip()
        category_name = self.category_combobox.get()
        notes = self.notes_entry.get("1.0", tk.END).strip()
        if not cust_id or not name or not category_name:
            messagebox.showwarning("輸入錯誤", "客戶 ID、名稱和分類為必填項！")
            return
        category_id = self.categories.get(category_name)
        if category_id is None: messagebox.showerror("錯誤", "選擇的分類不存在！"); return
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO customers (id, name, category_id, notes) VALUES (?, ?, ?, ?)",
                           (cust_id, name, category_id, notes))
            self.conn.commit()
            self.customer_id_entry.delete(0, tk.END); self.customer_name_entry.delete(0, tk.END); self.notes_entry.delete("1.0", tk.END)
            self.clear_filter()
            messagebox.showinfo("成功", f"客戶 {name} 已成功新增！")
        except sqlite3.IntegrityError: messagebox.showerror("錯誤", f"客戶 ID '{cust_id}' 已存在，請使用不同的 ID。")
        except Exception as e: messagebox.showerror("資料庫錯誤", f"發生錯誤: {e}")
    
    def add_category(self):
        """新增分類按鈕的處理函式"""
        new_cat_name = self.new_category_entry.get().strip()
        if not new_cat_name: messagebox.showwarning("輸入錯誤", "請輸入新分類的名稱！"); return
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (new_cat_name,))
            self.conn.commit()
            self.new_category_entry.delete(0, tk.END)
            self.load_categories()
            messagebox.showinfo("成功", f"分類 '{new_cat_name}' 已成功新增！")
        except sqlite3.IntegrityError: messagebox.showerror("錯誤", f"分類 '{new_cat_name}' 已存在！")
        except Exception as e: messagebox.showerror("資料庫錯誤", f"發生錯誤: {e}")

    def delete_customer(self):
        """刪除客戶按鈕的處理函式"""
        selected_item = self.tree.selection()
        if not selected_item: messagebox.showwarning("操作錯誤", "請先在列表中選擇一位要刪除的客戶。"); return
        customer_data = self.tree.item(selected_item, 'values')
        customer_id, customer_name = customer_data[0], customer_data[1]
        if messagebox.askyesno("確認刪除", f"確定要刪除客戶 '{customer_name}' (ID: {customer_id}) 嗎？\n此操作無法復原。"):
            try:
                cursor = self.conn.cursor(); cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,)); self.conn.commit()
                self.load_customers()
                messagebox.showinfo("成功", f"客戶 '{customer_name}' 已被成功刪除。")
            except Exception as e: messagebox.showerror("資料庫錯誤", f"刪除時發生錯誤: {e}")
            
    def save_customer_changes(self, edit_win, cust_id, name_entry, cat_combobox, notes_text):
        """儲存修改後客戶資料的函式"""
        new_name = name_entry.get().strip()
        new_category_name = cat_combobox.get()
        new_notes = notes_text.get("1.0", tk.END).strip()
        if not new_name or not new_category_name:
            messagebox.showwarning("輸入錯誤", "客戶名稱和分類為必填項！", parent=edit_win)
            return
        new_category_id = self.categories.get(new_category_name)
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE customers SET name = ?, category_id = ?, notes = ? WHERE id = ?", 
                           (new_name, new_category_id, new_notes, cust_id))
            self.conn.commit()
            edit_win.destroy()
            self.load_customers()
            messagebox.showinfo("成功", "客戶資料已成功更新！")
        except Exception as e:
            messagebox.showerror("資料庫錯誤", f"更新時發生錯誤: {e}", parent=edit_win)
            
    def delete_category(self):
        """刪除分類按鈕的處理函式"""
        category_name_to_delete = self.category_combobox.get()
        if not category_name_to_delete: messagebox.showwarning("操作錯誤", "請先從下拉選單中選擇一個要刪除的分類。"); return
        if messagebox.askyesno("確認刪除", f"確定要刪除分類 '{category_name_to_delete}' 嗎？\n注意：使用此分類的客戶將會失去分類連結。"):
            try:
                category_id = self.categories.get(category_name_to_delete)
                cursor = self.conn.cursor(); cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,)); self.conn.commit()
                self.load_categories()
                self.clear_filter()
                messagebox.showinfo("成功", f"分類 '{category_name_to_delete}' 已被刪除。")
            except Exception as e: messagebox.showerror("資料庫錯誤", f"刪除時發生錯誤: {e}")
                
    def on_closing(self):
        """處理主視窗關閉事件的函式"""
        if self.conn: self.conn.close()  # 關閉資料庫連線
        self.root.destroy()  # 銷毀主視窗

# --- 程式主入口 ---
if __name__ == "__main__":
    """
    這是 Python 腳本的標準主入口。
    當這個檔案被直接執行時，以下的程式碼會被觸發。
    如果這個檔案被其他檔案 import，則不會執行。
    """
    root = tk.Tk()  # 建立 Tkinter 的根視窗
    app = CustomerApp(root)  # 建立我們的應用程式類別實例
    root.protocol("WM_DELETE_WINDOW", app.on_closing)  # 攔截視窗關閉按鈕，執行自訂的 on_closing 函式
    root.mainloop()  # 進入 Tkinter 的事件迴圈，等待使用者操作