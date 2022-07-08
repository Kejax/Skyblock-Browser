import sys
from PyQt6 import QtWidgets, QtCore
from browser import Ui_MainWindow
import pathlib
import requests
import datetime


app_path = str(pathlib.Path(__file__).parent.absolute())
image_path = app_path + "/images/"


def image(name: str):
    return image_path + name + ".png"


class Worker(QtCore.QThread):

    items_collected = QtCore.pyqtSignal()
    items_indexed = QtCore.pyqtSignal(int)
    items_total = QtCore.pyqtSignal(int)

    def __init__(self, name, max_price):
        QtCore.QThread.__init__(self)
        self.name = name
        self.max_price = max_price
        self.auctions = {}
        self.items = 0
        self.last = None

    def run(self):
        response = requests.get("https://api.hypixel.net/skyblock/auctions")
        data = response.json()
        pages = data["totalPages"]
        self.items_total.emit(data["totalAuctions"])

        for i in range(pages):
            response = requests.get(f"https://api.hypixel.net/skyblock/auctions?page={i}")
            data = response.json()
            for auction in data["auctions"]:
                price = auction["highest_bid_amount"] if auction["highest_bid_amount"] > 0 else auction["starting_bid"]
                if (self.name is None) or (self.name.upper().lower() in auction["item_name"].upper().lower() and (self.max_price >= price or self.max_price == -1)):
                    self.auctions[auction["uuid"]] = auction
                self.items += 1
                self.items_indexed.emit(self.items)

        self.items_collected.emit()


class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.total = None
        self.worker = None
        self.name = None
        self.max_price = None
        self.setupUi(self)
        self.item_browser.setColumnCount(3)
        self.item_browser.setColumnWidth(0, 500)
        self.item_browser.setColumnWidth(1, 300)
        self.item_browser.setColumnWidth(2, 184)

        self.loading.setText("")

        self.item_browser.setHorizontalHeaderLabels(["Name", "Price", "Ends"])
        self.item_browser.setVerticalHeaderLabels([])

        self.name.returnPressed.connect(self.button_clicked)
        self.price.returnPressed.connect(self.button_clicked)

        self.pushButton.clicked.connect(self.button_clicked)
        self.auctions = {}

    def report_progress(self, count):
        self.loading.setText(f"Indexed {count} of {self.total} Items...")

    def total_(self, count):
        self.total = count

    def button_clicked(self):

        self.item_browser.clear()

        name = self.name.text() if len(self.name.text()) > 0 else None
        max_price = int(self.price.text() if len(self.price.text()) > 0 else "-1")

        self.worker = Worker(name, max_price)
        self.worker.items_collected.connect(self.add_items)
        self.worker.items_total.connect(self.total_)
        self.worker.items_indexed.connect(self.report_progress)

        self.worker.start()
        self.add_items()

    def add_items(self):
        item_count = 0
        auctions = [i for i in self.worker.auctions.values()]
        auctions = sorted(auctions, key=lambda d: d["starting_bid"] if d["highest_bid_amount"] <= 0 else d["highest_bid_amount"])
        self.item_browser.setRowCount(len(self.worker.auctions))
        for auction in auctions:
            price = auction["highest_bid_amount"] if auction["highest_bid_amount"] > 0 else auction["starting_bid"]

            items = [
                QtWidgets.QTableWidgetItem(auction["item_name"]),
                QtWidgets.QTableWidgetItem(str(price)),
                QtWidgets.QTableWidgetItem(
                    "Coming soon."
                    # datetime.datetime.fromtimestamp(int(auction["end"] / 1000)).strftime("%d. %m. %y - %H:%M:%S")
                )
            ]

            for item in items:
                item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
            self.item_browser.setItem(item_count, 0, items[0])
            self.item_browser.setItem(item_count, 1, items[1])
            self.item_browser.setItem(item_count, 2, items[2])

            item_count += 1
        self.loading.setText("")


app = QtWidgets.QApplication(sys.argv)
win = MyWindow()
win.show()
sys.exit(app.exec())
