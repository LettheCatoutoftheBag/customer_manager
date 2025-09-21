import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os

class CustomerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("簡易客戶分級系統")
        self.root.geometry("800x600") # 設定視窗大小

        # --- 資料庫初始化 ---
        self.db_name = "database.db"
        self.conn = self.init_database()
        
        # --- UI 介面設定 ---
        self.create_widgets()
        
        # --- 初始載入資料 ---
        self.load_categories()
        self.load_customers()

    def init_database(self):
        """初始化資料庫和資料表"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # 建立分類表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
        """)
        
        # 建立客戶表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category_id INTEGER,
            notes TEXT,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
        """)
        
        # 檢查是否有預設分類，若無則新增
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            default_categories = ["VIP 客戶", "活躍客戶", "潛在客戶", "新客戶"]
            for cat in default_categories:
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
        
        conn.commit()
        return conn

    def create_widgets(self):
        """建立所有 UI 元件"""
        # --- 主框架 ---
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- 左側：輸入和管理區 ---
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # --- 1. 新增客戶區 ---
        customer_frame = ttk.LabelFrame(left_frame, text="新增客戶", padding="10")
        customer_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(customer_frame, text="客戶 ID:").grid(row=0, column=0, sticky="w", pady=2)
        self.customer_id_entry = ttk.Entry(customer_frame, width=30)
        self.customer_id_entry.grid(row=0, column=1, sticky="ew", pady=2)

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

        # --- 2. 分類管理區 ---
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

        # --- 右側：客戶列表 ---
        right_frame = ttk.LabelFrame(main_frame, text="客戶列表", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

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

        # 新增垂直捲軸
        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_categories(self):
        """從資料庫載入分類並更新下拉選單"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM categories ORDER BY name")
        self.categories = {name: cat_id for cat_id, name in cursor.fetchall()}
        
        # 更新下拉選單
        category_names = list(self.categories.keys())
        self.category_combobox['values'] = category_names
        if category_names:
            self.category_combobox.current(0)

    def load_customers(self):
        """從資料庫載入客戶資料並更新列表"""
        # 清空現有列表
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        cursor = self.conn.cursor()
        query = """
        SELECT c.id, c.name, cat.name, c.notes
        FROM customers c
        LEFT JOIN categories cat ON c.category_id = cat.id
        ORDER BY c.name
        """
        cursor.execute(query)
        for row in cursor.fetchall():
            self.tree.insert("", tk.END, values=row)

    def add_customer(self):
        """新增一筆客戶資料"""
        cust_id = self.customer_id_entry.get().strip()
        name = self.customer_name_entry.get().strip()
        category_name = self.category_combobox.get()
        notes = self.notes_entry.get("1.0", tk.END).strip()

        if not cust_id or not name or not category_name:
            messagebox.showwarning("輸入錯誤", "客戶 ID、名稱和分類為必填項！")
            return

        category_id = self.categories.get(category_name)
        if category_id is None:
            messagebox.showerror("錯誤", "選擇的分類不存在！")
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO customers (id, name, category_id, notes) VALUES (?, ?, ?, ?)",
                           (cust_id, name, category_id, notes))
            self.conn.commit()
            
            # 清空輸入框並刷新列表
            self.customer_id_entry.delete(0, tk.END)
            self.customer_name_entry.delete(0, tk.END)
            self.notes_entry.delete("1.0", tk.END)
            self.load_customers()
            messagebox.showinfo("成功", f"客戶 {name} 已成功新增！")
        except sqlite3.IntegrityError:
            messagebox.showerror("錯誤", f"客戶 ID '{cust_id}' 已存在，請使用不同的 ID。")
        except Exception as e:
            messagebox.showerror("資料庫錯誤", f"發生錯誤: {e}")

    def add_category(self):
        """新增一個分類"""
        new_cat_name = self.new_category_entry.get().strip()
        if not new_cat_name:
            messagebox.showwarning("輸入錯誤", "請輸入新分類的名稱！")
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (new_cat_name,))
            self.conn.commit()
            
            self.new_category_entry.delete(0, tk.END)
            self.load_categories() # 重新載入分類
            messagebox.showinfo("成功", f"分類 '{new_cat_name}' 已成功新增！")
        except sqlite3.IntegrityError:
            messagebox.showerror("錯誤", f"分類 '{new_cat_name}' 已存在！")
        except Exception as e:
            messagebox.showerror("資料庫錯誤", f"發生錯誤: {e}")

    def delete_category(self):
        """刪除選中的分類"""
        category_name_to_delete = self.category_combobox.get()
        if not category_name_to_delete:
            messagebox.showwarning("操作錯誤", "請先從下拉選單中選擇一個要刪除的分類。")
            return
        
        if messagebox.askyesno("確認刪除", f"確定要刪除分類 '{category_name_to_delete}' 嗎？\n注意：使用此分類的客戶將會失去分類連結。"):
            try:
                category_id = self.categories.get(category_name_to_delete)
                cursor = self.conn.cursor()
                # 刪除分類本身
                cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
                self.conn.commit()
                
                self.load_categories()
                self.load_customers() # 刷新客戶列表，因為分類變了
                messagebox.showinfo("成功", f"分類 '{category_name_to_delete}' 已被刪除。")
            except Exception as e:
                messagebox.showerror("資料庫錯誤", f"刪除時發生錯誤: {e}")

    def on_closing(self):
        """關閉應用程式時的操作"""
        if self.conn:
            self.conn.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CustomerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing) # 處理視窗關閉事件
    root.mainloop()