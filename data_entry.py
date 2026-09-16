import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from db_connect import DB_Connection


load_dotenv()

CONNECTION_PARAMS = {
    "host": os.getenv("host"),
    "port": os.getenv("port"),
    "dbname": os.getenv("dbname"),
    "user": os.getenv("user"),
    "password": os.getenv("password"),
}


class PriceSpinBox(QDoubleSpinBox):
    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.lineEdit().selectAll()


class DataEntryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("POS Data Entry")
        self.resize(1000, 600)
        self.pending_products = []

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(self._build_coupon_panel(), 1)
        layout.addWidget(self._build_product_panel(), 2)
        self._refresh_coupons()
        self._refresh_products()

    def _build_coupon_panel(self):
        panel = QGroupBox("Add Coupon")
        layout = QVBoxLayout(panel)
        form = QFormLayout()
        form.setSpacing(12)

        self.coupon_code_input = QLineEdit()
        self.coupon_code_input.setPlaceholderText("e.g. SAVE10")
        form.addRow("Code", self.coupon_code_input)

        self.discount_input = QSpinBox()
        self.discount_input.setRange(1, 100)
        self.discount_input.setSuffix("%")
        form.addRow("Discount", self.discount_input)

        add_coupon_button = QPushButton("Add Coupon")
        add_coupon_button.setProperty("class", "primary-button")
        add_coupon_button.clicked.connect(self._add_coupon)
        form.addRow(add_coupon_button)
        layout.addLayout(form)

        layout.addWidget(QLabel("Saved Coupons"))
        self.coupon_table = QTableWidget(0, 3)
        self.coupon_table.setHorizontalHeaderLabels(["Code", "Discount", ""])
        self._configure_data_table(self.coupon_table)
        layout.addWidget(self.coupon_table, 1)

        manage_buttons = QHBoxLayout()
        refresh_button = QPushButton("Refresh")
        refresh_button.setProperty("class", "secondary-button")
        refresh_button.clicked.connect(self._refresh_coupons)
        manage_buttons.addWidget(refresh_button)
        layout.addLayout(manage_buttons)
        return panel

    def _build_product_panel(self):
        panel = QGroupBox("Add Products")
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)

        form_frame = QFrame()
        form = QFormLayout(form_frame)
        form.setSpacing(10)

        self.code_from_input = QSpinBox()
        self.code_from_input.setRange(1, 2147483647)
        self.code_from_input.valueChanged.connect(
            lambda: self.code_to_input.setValue(self.code_from_input.value()) if self.code_to_input.value() < self.code_from_input.value() else ...
            )
        form.addRow("Code from", self.code_from_input)

        self.code_to_input = QSpinBox()
        self.code_to_input.setRange(1, 2147483647)
        form.addRow("Code to", self.code_to_input)

        self.product_name_input = QLineEdit()
        self.product_name_input.setPlaceholderText("Product name")
        form.addRow("Name", self.product_name_input)

        self.price_input = PriceSpinBox()
        self.price_input.setRange(0, 999999.99)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix("$")
        form.addRow("Price", self.price_input)
        layout.addWidget(form_frame)

        buttons = QHBoxLayout()
        preview_button = QPushButton("Preview Range")
        preview_button.setProperty("class", "secondary-button")
        preview_button.clicked.connect(self._preview_products)
        buttons.addWidget(preview_button)

        add_products_button = QPushButton("Add Products")
        add_products_button.setProperty("class", "primary-button")
        add_products_button.clicked.connect(self._add_products)
        buttons.addWidget(add_products_button)
        layout.addLayout(buttons)

        self.preview_label = QLabel("No products queued")
        self.preview_label.setObjectName("formTitle")
        layout.addWidget(self.preview_label)

        layout.addWidget(QLabel("Saved Products"))
        self.product_table = QTableWidget(0, 5)
        self.product_table.setHorizontalHeaderLabels(["", "Code", "Name", "Price", ""])
        self._configure_data_table(self.product_table, allow_multiple=True)
        self.product_table.cellClicked.connect(self._toggle_product_checkbox)
        layout.addWidget(self.product_table, 1)

        manage_buttons = QHBoxLayout()
        refresh_button = QPushButton("Refresh")
        refresh_button.setProperty("class", "secondary-button")
        refresh_button.clicked.connect(self._refresh_products)
        manage_buttons.addWidget(refresh_button)

        bulk_delete_button = QPushButton("Delete Selected")
        bulk_delete_button.setProperty("class", "danger-button")
        bulk_delete_button.clicked.connect(self._delete_selected_products)
        manage_buttons.addWidget(bulk_delete_button)
        layout.addLayout(manage_buttons)
        return panel

    @staticmethod
    def _configure_data_table(table, allow_multiple=False):
        table.setSelectionBehavior(QTableWidget.SelectRows)
        selection_mode = QTableWidget.ExtendedSelection if allow_multiple else QTableWidget.SingleSelection
        table.setSelectionMode(selection_mode)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)

    def _refresh_coupons(self):
        try:
            with DB_Connection(table="cupons", **CONNECTION_PARAMS) as db:
                coupons = db.fetch_all_data()
        except Exception as error:
            QMessageBox.critical(self, "Coupons Not Loaded", str(error))
            return
        self.coupon_table.setRowCount(0)
        for coupon in coupons:
            row = self.coupon_table.rowCount()
            self.coupon_table.insertRow(row)
            self.coupon_table.setItem(row, 0, QTableWidgetItem(coupon["cuponcode"]))
            self.coupon_table.setItem(row, 1, QTableWidgetItem(f"{coupon['discount']}%"))
            delete_button = self._make_delete_button(
                lambda checked=False, code=coupon["cuponcode"]: self._delete_coupon(code)
            )
            self.coupon_table.setCellWidget(row, 2, delete_button)

    def _refresh_products(self):
        try:
            with DB_Connection(table="products", **CONNECTION_PARAMS) as db:
                products = db.fetch_all_data()
        except Exception as error:
            QMessageBox.critical(self, "Products Not Loaded", str(error))
            return
        self.product_table.setRowCount(0)
        for product in products:
            row = self.product_table.rowCount()
            self.product_table.insertRow(row)
            self.product_table.setCellWidget(row, 0, self._make_selection_checkbox())
            self.product_table.setItem(row, 1, QTableWidgetItem(str(product["code"])))
            self.product_table.setItem(row, 2, QTableWidgetItem(product["product_name"]))
            self.product_table.setItem(row, 3, QTableWidgetItem(f"${product['price']:.2f}"))
            delete_button = self._make_delete_button(
                lambda checked=False, code=product["code"]: self._delete_product(code)
            )
            self.product_table.setCellWidget(row, 4, delete_button)

    @staticmethod
    def _make_selection_checkbox():
        checkbox = QCheckBox()
        checkbox.setToolTip("Select product")
        checkbox.setAccessibleName("Select product")
        return checkbox

    def _toggle_product_checkbox(self, row, column):
        if column not in (1, 2, 3):
            return
        checkbox = self.product_table.cellWidget(row, 0)
        if checkbox is not None:
            checkbox.setChecked(not checkbox.isChecked())

    @staticmethod
    def _make_delete_button(callback):
        button = QPushButton("×")
        button.setProperty("class", "remove-button")
        button.setToolTip("Delete")
        button.setAccessibleName("Delete")
        button.setFixedWidth(32)
        button.clicked.connect(callback)
        return button

    def _delete_coupon(self, code):
        try:
            with DB_Connection(table="cupons", **CONNECTION_PARAMS) as db:
                db.del_data(cuponcode=code)
        except Exception as error:
            QMessageBox.critical(self, "Coupon Not Deleted", str(error))
            return
        self._refresh_coupons()

    def _delete_product(self, code):
        try:
            with DB_Connection(table="products", **CONNECTION_PARAMS) as db:
                db.del_data(code=code)
        except Exception as error:
            QMessageBox.critical(self, "Product Not Deleted", str(error))
            return
        self._refresh_products()

    def _delete_selected_products(self):
        rows = [
            row
            for row in range(self.product_table.rowCount())
            if self.product_table.cellWidget(row, 0).isChecked()
        ]
        if not rows:
            QMessageBox.information(self, "No Products Selected", "Check one or more products to delete.")
            return

        codes = [int(self.product_table.item(row, 1).text()) for row in rows]
        answer = QMessageBox.warning(
            self,
            "Delete Products",
            f"Delete {len(codes)} selected product(s)? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        try:
            with DB_Connection(table="products", **CONNECTION_PARAMS) as db:
                for code in codes:
                    db.del_data(code=code)
        except Exception as error:
            QMessageBox.critical(self, "Products Not Deleted", str(error))
            return
        self._refresh_products()

    def _read_product_form(self):
        code_from = self.code_from_input.value()
        code_to = self.code_to_input.value()
        name = self.product_name_input.text().strip()
        if code_from > code_to:
            QMessageBox.warning(self, "Invalid Code Range", "Code from must be less than or equal to code to.")
            return None
        if not name:
            QMessageBox.warning(self, "Missing Product Name", "Enter a product name before continuing.")
            return None
        return code_from, code_to, name, self.price_input.value()

    def _preview_products(self):
        values = self._read_product_form()
        if values is None:
            return
        code_from, code_to, name, price = values
        self.pending_products = [
            {"code": code, "product_name": name, "price": price}
            for code in range(code_from, code_to + 1)
        ]
        self.preview_label.setText(f"{len(self.pending_products)} product(s) queued")

    def _add_coupon(self):
        code = self.coupon_code_input.text().strip()
        if not code:
            QMessageBox.warning(self, "Missing Coupon Code", "Enter a coupon code before continuing.")
            return
        try:
            with DB_Connection(table="cupons", **CONNECTION_PARAMS) as db:
                db.push_data(cuponcode=code, discount=self.discount_input.value())
        except Exception as error:
            QMessageBox.critical(self, "Coupon Not Added", str(error))
            return
        self.coupon_code_input.clear()
        self.discount_input.setValue(1)
        self._refresh_coupons()
        QMessageBox.information(self, "Coupon Added", f"Coupon {code} was added.")

    def _add_products(self):
        if not self.pending_products:
            self._preview_products()
        if not self.pending_products:
            return
        try:
            with DB_Connection(table="products", **CONNECTION_PARAMS) as db:
                for pending_product in self.pending_products:
                    db.push_data(**pending_product)
        except Exception as error:
            QMessageBox.critical(self, "Products Not Added", str(error))
            return
        count = len(self.pending_products)
        self.pending_products = []
        self.preview_label.setText("No products queued")
        self._refresh_products()
        QMessageBox.information(self, "Products Added", f"{count} product(s) were added.")


def load_stylesheet(app):
    qss_path = Path(__file__).parent / "pos_style.qss"
    app.setStyleSheet(qss_path.read_text())


def main():
    app = QApplication(sys.argv)
    load_stylesheet(app)
    window = DataEntryWindow()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()