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
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from db_connect import DB_Connection
from dotenv import load_dotenv
import os
load_dotenv()

conn_params = dict(
    host=os.getenv("host"),
    port=os.getenv("port"),
    dbname=os.getenv("dbname"),
    user=os.getenv("user"),
    password=os.getenv("password"),
)

SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 16
SPACE_LG = 24

# sample_cupon = [
#     {"cuponcode": "SAVE10", "discount": 10},
#     {"cuponcode": "WELCOME20", "discount": 20},
# ]

# --- hardcoded sample product data: swap this for a DB query later ---
# SAMPLE_PRODUCTS = [
#     {"code": "1001", "product_name": "Coffee", "price": 3.50},
#     {"code": "1002", "product_name": "Sandwich", "price": 6.00},
#     {"code": "1003", "product_name": "Croissant", "price": 2.75},
#     {"code": "1004", "product_name": "Orange Juice", "price": 3.00},
#     {"code": "1005", "product_name": "Muffin", "price": 2.50},
#     {"code": "1006", "product_name": "Bottled Water", "price": 1.50},
#     {"code": "1007", "product_name": "Bagel", "price": 2.25},
#     {"code": "1008", "product_name": "Iced Tea", "price": 3.25},
# ]

with DB_Connection(
    table="products",
    **conn_params
) as db:
    SAMPLE_PRODUCTS = db.fetch_data()
with DB_Connection(
    table='cupons',
    **conn_params
) as db:
    sample_cupon = db.fetch_data()



class ProductTile(QPushButton):
    """A clickable product card in the grid."""

    def __init__(self, product: dict, on_click):
        super().__init__(f"{product['product_name']}\n${product['price']:.2f}")
        self.product = product
        self.setProperty("class", "product-tile")
        self.setMinimumHeight(70)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(lambda: on_click(product))


class ProductPanel(QFrame):
    """Left side: search/barcode entry, product grid, manual entry form."""

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

        # --- search / barcode field ---
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Scan barcode or search by name…")
        self.search_box.setObjectName("searchBox")
        self.search_box.textChanged.connect(self._filter_grid)
        self.search_box.returnPressed.connect(self._handle_scan)
        layout.addWidget(self.search_box)

        # --- product grid ---
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(SPACE_SM)
        self.tiles: list[ProductTile] = []
        for i, product in enumerate(SAMPLE_PRODUCTS):
            tile = ProductTile(product, self.on_add)
            self.tiles.append(tile)
            self.grid_layout.addWidget(tile, i // 3, i % 3)
        layout.addWidget(self.grid_widget)

        layout.addStretch(1)

        # --- manual entry form ---
        form_frame = QFrame()
        form_frame.setObjectName("manualForm")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(SPACE_SM)

        form_title = QLabel("Add custom item")
        form_title.setObjectName("formTitle")
        form_layout.addWidget(form_title)

        row1 = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Item name")
        row1.addWidget(self.name_input, 2)

        self.price_input = QDoubleSpinBox()
        self.price_input.setPrefix("$")
        self.price_input.setMaximum(9999.99)
        self.price_input.setDecimals(2)
        row1.addWidget(self.price_input, 1)

        self.qty_input = QSpinBox()
        self.qty_input.setMinimum(1)
        self.qty_input.setMaximum(999)
        row1.addWidget(self.qty_input, 1)
        form_layout.addLayout(row1)

        add_custom_btn = QPushButton("Add Custom Item")
        add_custom_btn.setProperty("class", "secondary-button")
        add_custom_btn.clicked.connect(self._add_custom)
        form_layout.addWidget(add_custom_btn)

        layout.addWidget(form_frame)

    def _filter_grid(self, text: str):
        text = text.strip().lower()
        for tile in self.tiles:
            match = text in tile.product["product_name"].lower() or text in tile.product["code"]
            tile.setVisible(match or text == "")

    def _handle_scan(self):
        code = self.search_box.text().strip()
        for product in SAMPLE_PRODUCTS:
            if product["code"] == code:
                self.on_add(product)
                self.search_box.clear()
                return
        # no exact code match — if exactly one product is currently visible, add that one
        visible = [t.product for t in self.tiles if t.isVisible()]
        if len(visible) == 1:
            self.on_add(visible[0])
            self.search_box.clear()

    def _add_custom(self):
        name = self.name_input.text().strip()
        if not name:
            return
        product = {
            "code": f"CUSTOM-{name.lower()}",
            "product_name": name,
            "price": self.price_input.value(),
        }
        self.on_add(product, qty=self.qty_input.value())
        self.name_input.clear()
        self.price_input.setValue(0)
        self.qty_input.setValue(1)


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
        self._custom_counter = 0

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
        code = product["code"]
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
        for cupon in sample_cupon:
            if cupon["cuponcode"].lower() == cupon_code.lower():
                self.cart_panel.set_discount(cupon["discount"], cupon["cuponcode"])
                return
        self.cart_panel.set_discount(0, "")
        QMessageBox.warning(self, "Invalid Coupon", "That coupon code is not valid.")

    def purchase(self):
        if not self.cart:
            QMessageBox.information(self, "Cart Empty", "Add items to the cart before purchasing.")
            return
        subtotal = sum(item["price"] * item["qty"] for item in self.cart.values())
        total = subtotal * (1 - self.cart_panel.discount / 100)
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
