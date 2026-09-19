import sys
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

    def purchase(self):
        if not self.cart:
            QMessageBox.information(self, "Cart Empty", "Add items to the cart before purchasing.")
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

        QMessageBox.information(self, "Purchase Complete", f"Charged ${total:.2f}. Thank you!")
        self.cart.clear()
        self.cart_panel.clear_cupon()
        self.cart_panel.render_cart(self.cart)


def load_stylesheet(app: QApplication):
    qss_path = Path(__file__).parent / "pos_style.qss"
    app.setStyleSheet(qss_path.read_text())


def main():
    app = QApplication(sys.argv)
    load_stylesheet(app)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()