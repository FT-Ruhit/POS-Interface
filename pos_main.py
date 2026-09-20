import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from db_connect import DB_Connection

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 16
SPACE_LG = 24





class ProductPanel(QFrame):
    """Left side: add a product by its real DB code, add a one-off custom
    item, or tap a quick-item tile — all three now go through the DB or
    are explicitly marked as non-DB (CUSTOM-)."""

    def __init__(self, on_add):
        super().__init__()
        self.on_add = on_add
        self.setObjectName("productPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE_LG, SPACE_LG, SPACE_MD, SPACE_LG)
        layout.setSpacing(SPACE_MD)

        heading = QLabel("Products")
        heading.setObjectName("panelTitle")
        layout.addWidget(heading)

        # --- add by real product code (looked up in the DB) ---
        lookup_frame = QFrame()
        lookup_frame.setObjectName("manualForm")
        lookup_layout = QVBoxLayout(lookup_frame)
        lookup_layout.setSpacing(SPACE_SM)

        lookup_title = QLabel("Add by code")
        lookup_title.setObjectName("formTitle")
        lookup_layout.addWidget(lookup_title)

        lookup_row = QHBoxLayout()
        self.item_code_input = QLineEdit()
        self.item_code_input.setPlaceholderText("Product code")
        self.item_code_input.returnPressed.connect(self._add_by_code)
        lookup_row.addWidget(self.item_code_input, 2)

        lookup_btn = QPushButton("Add")
        lookup_btn.setProperty("class", "secondary-button")
        lookup_btn.clicked.connect(self._add_by_code)
        lookup_row.addWidget(lookup_btn, 1)
        lookup_layout.addLayout(lookup_row)
        layout.addWidget(lookup_frame)

        # --- one-off custom item, explicitly not a DB lookup ---
        custom_frame = QFrame()
        custom_frame.setObjectName("manualForm")
        custom_layout = QVBoxLayout(custom_frame)
        custom_layout.setSpacing(SPACE_SM)

        custom_title = QLabel("Add custom item")
        custom_title.setObjectName("formTitle")
        custom_layout.addWidget(custom_title)

        self.custom_name_input = QLineEdit()
        self.custom_name_input.setPlaceholderText("Item name")
        custom_layout.addWidget(self.custom_name_input)

        custom_row = QHBoxLayout()
        self.custom_price_input = QDoubleSpinBox()
        self.custom_price_input.setPrefix("$")
        self.custom_price_input.setMaximum(9999.99)
        self.custom_price_input.setDecimals(2)
        custom_row.addWidget(self.custom_price_input, 1)

        add_custom_btn = QPushButton("Add")
        add_custom_btn.setProperty("class", "secondary-button")
        add_custom_btn.clicked.connect(self._add_custom)
        custom_row.addWidget(add_custom_btn, 1)
        custom_layout.addLayout(custom_row)
        layout.addWidget(custom_frame)

        layout.addStretch(1)

        # --- quick items: predefined items, tap to add instantly ---
        quick_items_label = QLabel("Quick Items")
        quick_items_label.setObjectName("formTitle")
        layout.addWidget(quick_items_label)

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(SPACE_SM)
        layout.addWidget(self.grid_widget)

        self._load_quick_items()

    def _load_quick_items(self, limit=6):
        try:
            with DB_Connection(table="quickitems") as db:
                quick_items = db.fetch_all_data()
        except Exception as error:
            QMessageBox.critical(self, "Quick Items Not Loaded", str(error))
            return

        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for i, quick_item in enumerate(quick_items):
            tile = QPushButton(
                f"{quick_item['product_name']}\n${quick_item['price']:.2f}"
            )
            tile.setProperty("class", "product-tile")
            tile.setMinimumHeight(70)
            tile.setCursor(Qt.PointingHandCursor)
            tile.clicked.connect(
                lambda checked=False, item=dict(quick_item): self._add_quick_item(item)
            )
            self.grid_layout.addWidget(tile, i // 3, i % 3)

    def _add_quick_item(self, quick_item):
        self.on_add({
            "code": f"QUICK-{quick_item['product_name']}",
            "product_name": quick_item["product_name"],
            "price": float(quick_item["price"]),
        })

    def _add_db_product(self, product):
        self.on_add({
            "code": str(product["code"]),
            "product_name": product["product_name"],
            "price": float(product["price"]),
        })

    def _add_by_code(self):
        code_text = self.item_code_input.text().strip()
        if not code_text:
            return
        try:
            code = int(code_text)
        except ValueError:
            QMessageBox.warning(self, "Invalid Code", "Product code must be a number.")
            return

        try:
            with DB_Connection(table="products") as db:
                results = db.fetch_data(code=code)
        except Exception as error:
            QMessageBox.critical(self, "Lookup Failed", str(error))
            return

        if not results:
            QMessageBox.warning(self, "Not Found", f"No product with code {code}.")
            return

        self._add_db_product(results)
        self.item_code_input.clear()

    def _add_custom(self):
        name = self.custom_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Enter a name for the custom item.")
            return
        product = {
            "code": f"CUSTOM-{name}",
            "product_name": name,
            "price": self.custom_price_input.value(),
        }
        self.on_add(product)
        self.custom_name_input.clear()
        self.custom_price_input.setValue(0)


class CustomerPanel(QFrame):
    """Phone-first customer lookup, the way most POS front counters work:
    type/scan the phone number, and either the name comes back for a
    returning customer, or the cashier is prompted to enter one for a
    new customer, which gets saved for next time."""

    def __init__(self):
        super().__init__()
        self.setObjectName("manualForm")
        self._customer = None       # resolved {"name", "phone"} or None (walk-in)
        self._pending_phone = None  # phone looked up with no match yet, awaiting a name

        layout = QVBoxLayout(self)
        layout.setSpacing(SPACE_SM)

        title = QLabel("Customer")
        title.setObjectName("formTitle")
        layout.addWidget(title)

        phone_row = QHBoxLayout()
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone number")
        self.phone_input.returnPressed.connect(self._lookup_customer)
        self.phone_input.textEdited.connect(self._on_phone_edited)
        phone_row.addWidget(self.phone_input)
        layout.addLayout(phone_row)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Customer name")
        self.name_input.setEnabled(False)
        self.name_input.returnPressed.connect(self._save_new_customer)
        layout.addWidget(self.name_input)

        self.status_label = QLabel()
        self.status_label.setObjectName("customerStatusLabel")
        layout.addWidget(self.status_label)

    def _lookup_customer(self):
        phone = self.phone_input.text().strip()
        if not phone:
            QMessageBox.warning(self, "Missing Phone", "Enter a phone number to look up.")
            return

        try:
            with DB_Connection(table="customers") as db:
                result = db.fetch_data(phone=phone)
        except Exception as error:
            QMessageBox.critical(self, "Lookup Failed", str(error))
            return

        if result:
            name = result["name"]
            self._customer = {"name": name, "phone": phone}
            self._pending_phone = None
            self.name_input.setText(name)
            self.name_input.setEnabled(False)
            self.status_label.setText(f"Welcome back, {name}!")
        else:
            self._customer = None
            self._pending_phone = phone
            self.name_input.clear()
            self.name_input.setEnabled(True)
            self.name_input.setFocus()
            self.status_label.setText("New customer — enter name and press Enter to save")

    def _save_new_customer(self):
        if self._pending_phone is None:
            return
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Enter a name for the new customer.")
            return

        try:
            with DB_Connection(table="customers") as db:
                db.push_data(name=name, phone=self._pending_phone)
        except Exception as error:
            QMessageBox.critical(self, "Could Not Save Customer", str(error))
            return

        self._customer = {"name": name, "phone": self._pending_phone}
        self._pending_phone = None
        self.name_input.setEnabled(False)
        self.status_label.setText(f"Saved new customer: {name}")

    def _on_phone_edited(self, text):
        phone = text.strip()
        if not phone:
            self._customer = None
            self._pending_phone = None
            self.name_input.clear()
            self.name_input.setEnabled(False)
            self.status_label.clear()
            return

        try:
            with DB_Connection(table="customers") as db:
                result = db.fetch_data(phone=phone)
        except Exception as error:
            QMessageBox.critical(self, "Lookup Failed", str(error))
            self._customer = None
            self._pending_phone = None
            self.name_input.clear()
            self.name_input.setEnabled(False)
            self.status_label.clear()
            return

        if result:
            name = result["name"]
            self._customer = {"name": name, "phone": phone}
            self._pending_phone = None
            self.name_input.setText(name)
            self.name_input.setEnabled(False)
            self.status_label.setText(f"Welcome back, {name}!")
            return

        # Do not steal focus from the phone field while typing. A DB lookup is
        # enough to populate the name automatically when a match exists; if there
        # is no match, the customer can still be added manually without the UI
        # jumping to the name box.
        self._customer = None
        self._pending_phone = phone
        self.name_input.clear()
        self.name_input.setEnabled(True)
        self.status_label.setText("New customer — enter name and press Enter to save")

    def has_pending_entry(self) -> bool:
        """True when a phone number was looked up, came back new, and is
        still waiting on a name to be entered and saved."""
        return self._pending_phone is not None

    def get_customer(self):
        """Resolved {"name", "phone"} for a walk-in-free sale, or None
        for a walk-in sale (no phone number entered at all)."""
        return self._customer

    def reset(self):
        self.phone_input.clear()
        self.name_input.clear()
        self.name_input.setEnabled(False)
        self.status_label.clear()
        self._customer = None
        self._pending_phone = None


class CartPanel(QFrame):
    """Right side: cart table with editable quantities, total, purchase button."""

    def __init__(self, on_change_qty, on_remove, on_purchase, on_apply_cupon):
        super().__init__()
        self.on_change_qty = on_change_qty
        self.on_remove = on_remove
        self.on_purchase = on_purchase
        self.on_apply_cupon = on_apply_cupon
        self.discount = 0
        self._cart = {}
        self.setObjectName("cartPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE_MD, SPACE_LG, SPACE_LG, SPACE_LG)
        layout.setSpacing(SPACE_MD)

        heading = QLabel("Cart")
        heading.setObjectName("panelTitle")
        layout.addWidget(heading)

        self.customer_panel = CustomerPanel()
        layout.addWidget(self.customer_panel)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Item", "Price", "Qty", "Subtotal", ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table, 1)

        cupon_row = QHBoxLayout()
        self.cupon_input = QLineEdit()
        self.cupon_input.setPlaceholderText("Coupon code")
        cupon_row.addWidget(self.cupon_input)

        apply_cupon_btn = QPushButton("Apply")
        apply_cupon_btn.setProperty("class", "secondary-button")
        apply_cupon_btn.clicked.connect(self._apply_cupon)
        cupon_row.addWidget(apply_cupon_btn)
        layout.addLayout(cupon_row)

        self.cupon_label = QLabel()
        self.cupon_label.setObjectName("cuponLabel")
        layout.addWidget(self.cupon_label)

        self.total_label = QLabel("Total: $0.00")
        self.total_label.setObjectName("totalLabel")
        self.total_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.total_label)

        purchase_btn = QPushButton("Purchase")
        purchase_btn.setObjectName("purchaseButton")
        purchase_btn.setCursor(Qt.PointingHandCursor)
        purchase_btn.clicked.connect(self.on_purchase)
        layout.addWidget(purchase_btn)

    def render_cart(self, cart: dict):
        self._cart = cart
        self.table.setRowCount(0)
        total = 0.0

        for code, item in cart.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            subtotal = item["price"] * item["qty"]
            total += subtotal

            self.table.setItem(row, 0, QTableWidgetItem(item["product_name"]))
            self.table.setItem(row, 1, QTableWidgetItem(f"${item['price']:.2f}"))

            qty_widget = self._make_qty_widget(code, item["qty"])
            self.table.setCellWidget(row, 2, qty_widget)

            self.table.setItem(row, 3, QTableWidgetItem(f"${subtotal:.2f}"))

            remove_btn = QPushButton("✕")
            remove_btn.setProperty("class", "remove-button")
            remove_btn.setCursor(Qt.PointingHandCursor)
            remove_btn.clicked.connect(lambda checked, c=code: self.on_remove(c))
            self.table.setCellWidget(row, 4, remove_btn)

        discounted_total = total * (1 - self.discount / 100)
        self.cupon_label.setText(f"Discount: {self.discount:.0f}%" if self.discount else "")
        if self.discount:
            self.total_label.setText(
                f'<span style="color:#9a9a9a;"><s>Total: ${total:.2f}</s></span><br>'
                f'<span style="color:#0a84ff;">Total: ${discounted_total:.2f}</span>'
            )
        else:
            self.total_label.setText(f"Total: ${total:.2f}")

    def _apply_cupon(self):
        # print(self.cupon_input.text().strip())
        self.on_apply_cupon(self.cupon_input.text().strip())

    def set_discount(self, discount: int, cupon_code: str):
        self.discount = discount
        self.cupon_input.setText(cupon_code)
        self.render_cart(self._cart)

    def clear_cupon(self):
        self.discount = 0
        self.cupon_input.clear()
        self.cupon_label.clear()

    def clear_customer(self):
        self.customer_panel.reset()

    def _make_qty_widget(self, code: str, qty: int) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE_XS)

        minus_btn = QPushButton("–")
        minus_btn.setProperty("class", "qty-button")
        minus_btn.clicked.connect(lambda: self.on_change_qty(code, -1))

        qty_label = QLabel(str(qty))
        qty_label.setAlignment(Qt.AlignCenter)
        qty_label.setFixedWidth(24)

        plus_btn = QPushButton("+")
        plus_btn.setProperty("class", "qty-button")
        plus_btn.clicked.connect(lambda: self.on_change_qty(code, 1))

        row.addWidget(minus_btn)
        row.addWidget(qty_label)
        row.addWidget(plus_btn)
        return container


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("POS Terminal")
        self.resize(1000, 600)

        self.cart: dict[str, dict] = {}

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.product_panel = ProductPanel(on_add=self.add_to_cart)
        self.cart_panel = CartPanel(
            on_change_qty=self.change_qty,
            on_remove=self.remove_item,
            on_purchase=self.purchase,
            on_apply_cupon=self.apply_cupon,
        )

        layout.addWidget(self.product_panel, 3)
        layout.addWidget(self.cart_panel, 2)

        self.cart_panel.render_cart(self.cart)

    def add_to_cart(self, product: dict, qty: int = 1):
        # Cart is keyed by product code, not name — two different DB
        # products that happen to share a name no longer collapse into
        # one cart line.
        code = str(product["code"])
        if code in self.cart:
            self.cart[code]["qty"] += qty
        else:
            self.cart[code] = {
                "product_name": product["product_name"],
                "price": product["price"],
                "qty": qty,
            }
        self.cart_panel.render_cart(self.cart)

    def change_qty(self, code: str, delta: int):
        if code not in self.cart:
            return
        self.cart[code]["qty"] += delta
        if self.cart[code]["qty"] <= 0:
            del self.cart[code]
        self.cart_panel.render_cart(self.cart)

    def remove_item(self, code: str):
        self.cart.pop(code, None)
        self.cart_panel.render_cart(self.cart)

    def apply_cupon(self, cupon_code: str):
        try:
            with DB_Connection(table='cupons') as db:
                cupon = db.fetch_data(
                    cuponcode = cupon_code
                )
                # print(cupon)
                self.cart_panel.set_discount(int(cupon["discount"]), cupon["cuponcode"])
                return
        except:
            self.cart_panel.set_discount(0, "")
            QMessageBox.warning(self, "Invalid Coupon", "That coupon code is not valid.")

    def generate_receipt_pdf(self):
        if not self.cart:
            return None

        subtotal = sum(item["price"] * item["qty"] for item in self.cart.values())
        discount_percent = self.cart_panel.discount
        discount_amount = subtotal * (discount_percent / 100)
        total = subtotal - discount_amount
        customer = self.cart_panel.customer_panel.get_customer()

        receipt_dir = Path(__file__).parent / "receipts"
        receipt_dir.mkdir(exist_ok=True)

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = receipt_dir / f"receipt_{stamp}.pdf"

        # Drawn directly with reportlab instead of going through
        # QTextDocument/QPrinter — that path renders HTML "px" sizes as
        # literal device pixels at the printer's DPI (1200 on most
        # systems), which shrank everything but the heading to invisible
        # specks. reportlab draws in points from the start, so there's no
        # unit mismatch to trip over, and no Qt print backend required.
        page_width, page_height = letter
        margin = 20 * mm
        line_height = 14
        col_qty_x = page_width - margin - 100
        col_amount_x = page_width - margin

        pdf = canvas.Canvas(str(file_path), pagesize=letter)

        y = page_height - margin
        pdf.setFont("Courier-Bold", 16)
        pdf.drawCentredString(page_width / 2, y, "POS TERMINAL")
        y -= 20

        pdf.setFont("Courier", 10)
        pdf.drawCentredString(page_width / 2, y, f"Receipt #: {stamp}")
        y -= line_height
        pdf.drawCentredString(
            page_width / 2, y, datetime.now().strftime("%d-%b-%Y %H:%M:%S")
        )
        y -= line_height
        phn_number = customer['phone'][:2] + '*'*6 + customer['phone'][-3:]
        pdf.drawCentredString(
            page_width / 2,
            y,
            f"Customer: {customer['name']} ({phn_number})" if customer else "Customer: Walk-in",
        )
        y -= line_height

        def dashed_rule(y):
            pdf.saveState()
            pdf.setDash(3, 2)
            pdf.line(margin, y, page_width - margin, y)
            pdf.restoreState()

        dashed_rule(y)
        y -= line_height

        pdf.setFont("Courier-Bold", 10)
        pdf.drawString(margin, y, "Item")
        pdf.drawRightString(col_qty_x, y, "Qty / Price")
        pdf.drawRightString(col_amount_x, y, "Amount")
        y -= line_height

        pdf.setFont("Courier", 10)
        for item in self.cart.values():
            line_total = item["price"] * item["qty"]
            pdf.drawString(margin, y, item["product_name"][:30])
            pdf.drawRightString(col_qty_x, y, f"{item['qty']} x ${item['price']:.2f}")
            pdf.drawRightString(col_amount_x, y, f"${line_total:.2f}")
            y -= line_height

        dashed_rule(y)
        y -= line_height

        pdf.drawString(margin, y, "Subtotal")
        pdf.drawRightString(col_amount_x, y, f"${subtotal:.2f}")
        y -= line_height

        if discount_percent:
            pdf.drawString(margin, y, f"Discount ({discount_percent:.0f}%)")
            pdf.drawRightString(col_amount_x, y, f"-${discount_amount:.2f}")
            y -= line_height

        pdf.setFont("Courier-Bold", 11)
        pdf.drawString(margin, y, "Total")
        pdf.drawRightString(col_amount_x, y, f"${total:.2f}")
        y -= line_height

        dashed_rule(y)
        y -= 20

        pdf.setFont("Courier", 10)
        pdf.drawCentredString(page_width / 2, y, "Thank you! Please come again.")

        pdf.save()

        return str(file_path)

    def purchase(self):
        if not self.cart:
            QMessageBox.information(self, "Cart Empty", "Add items to the cart before purchasing.")
            return

        # A phone number was looked up, came back as a new customer, and
        # is still waiting on a name — don't let the sale complete half
        # wired to nobody. Either finish it or clear the phone number.
        if self.cart_panel.customer_panel.has_pending_entry():
            QMessageBox.warning(
                self,
                "Customer Name Needed",
                "Enter and save the new customer's name before completing the "
                "purchase, or clear the phone number for a walk-in sale.",
            )
            return

        subtotal = sum(item["price"] * item["qty"] for item in self.cart.values())
        total = subtotal * (1 - self.cart_panel.discount / 100)

        # Only coded products from the products table are removed after purchase.
        product_codes = [int(code) for code in self.cart.keys() if code.isdigit()]

        if product_codes:
            try:
                with DB_Connection(table="products") as db:
                    for product_code in product_codes:
                        db.del_data(
                            code = product_code
                        )
            except Exception as error:
                QMessageBox.critical(self, "Purchase Not Completed", f"Could not remove purchased products: {error}")
                return

        try:
            receipt_path = self.generate_receipt_pdf()
        except Exception as error:
            # Stock has already been deducted above, so don't silently drop
            # the sale on the floor if only the PDF step fails — surface it
            # and still confirm the charge.
            receipt_path = None
            QMessageBox.warning(
                self,
                "Receipt Not Generated",
                f"Sale was completed but the receipt PDF could not be created: {error}",
            )

        if receipt_path:
            QMessageBox.information(
                self,
                "Purchase Complete",
                f"Charged ${total:.2f}. Thank you!\nReceipt saved to:\n{receipt_path}",
            )
        else:
            QMessageBox.information(self, "Purchase Complete", f"Charged ${total:.2f}. Thank you!")

        self.cart.clear()
        self.cart_panel.clear_cupon()
        self.cart_panel.clear_customer()
        self.cart_panel.render_cart(self.cart)


def detect_system_color_scheme(app: QApplication):
    try:
        style_hints = app.styleHints()
        scheme = style_hints.colorScheme()
        if scheme == Qt.ColorScheme.Dark:
            return "dark"
        if scheme == Qt.ColorScheme.Light:
            return "light"
    except Exception:
        pass

    return "dark"


def load_stylesheet(app: QApplication):
    theme = detect_system_color_scheme(app)
    qss_name = "dark_style.qss" if theme == "dark" else "light_style.qss"
    qss_path = Path(__file__).parent / qss_name
    app.setStyleSheet(qss_path.read_text())


def connect_system_theme_listener(app: QApplication):
    try:
        app.styleHints().colorSchemeChanged.connect(lambda _scheme: load_stylesheet(app))
    except Exception:
        pass


def main():
    app = QApplication(sys.argv)
    load_stylesheet(app)
    connect_system_theme_listener(app)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()