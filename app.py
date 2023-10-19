import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLineEdit,
    QGridLayout,
    QCalendarWidget,
    QMessageBox,
    QHBoxLayout,
    QTextEdit,
)
from PyQt5.QtSql import QSqlDatabase, QSqlQuery


class AppointmentsApp(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize UI and Database
        self.init_db()
        self.init_ui()

    def init_db(self):
        """Set up an SQLite database and create the appointments table."""
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(":memory:")  # In-memory database for simplicity.

        if not self.db.open():
            QMessageBox.critical(self, "Database Error", "Database Connection Failed!")
            sys.exit(1)

        query = QSqlQuery()
        query.exec_(
            """
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY,
                name TEXT,
                ssn TEXT,
                address TEXT,
                phone TEXT,
                date DATE,
                time TEXT
            )
            """
        )

    def init_ui(self):
        """Set up the User Interface for the appointment application."""
        layout = QVBoxLayout()

        # Patient Info Inputs
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Name")
        layout.addWidget(self.name_input)

        self.ssn_input = QLineEdit(self)
        self.ssn_input.setPlaceholderText("Social Security Number (13 digits)")
        layout.addWidget(self.ssn_input)

        self.address_input = QLineEdit(self)
        self.address_input.setPlaceholderText("Address")
        layout.addWidget(self.address_input)

        self.phone_input = QLineEdit(self)
        self.phone_input.setPlaceholderText("Phone Number")
        layout.addWidget(self.phone_input)

        # Time slots buttons
        self.times = [
            QPushButton(f"{i:02d}:{j:02d}", self)
            for i in range(9, 18)
            for j in range(0, 60, 15)
        ]
        time_grid = QGridLayout()
        for idx, btn in enumerate(self.times):
            btn.setCheckable(True)
            time_grid.addWidget(btn, idx // 4, idx % 4)
        layout.addLayout(time_grid)

        # Action buttons
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Save Appointment", self)
        save_btn.clicked.connect(self.save_appointment)
        btn_layout.addWidget(save_btn)

        view_btn = QPushButton("View Appointment", self)
        view_btn.clicked.connect(self.view_appointment)
        btn_layout.addWidget(view_btn)

        edit_btn = QPushButton("Edit Appointment", self)
        edit_btn.clicked.connect(self.edit_appointment)
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete Appointment", self)
        delete_btn.clicked.connect(self.delete_appointment)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)

        # Display reservations for selected date
        self.reservations_display = QTextEdit(self)
        self.reservations_display.setReadOnly(True)
        layout.addWidget(self.reservations_display)

        # Calendar widget
        self.calendar = QCalendarWidget(self)
        self.calendar.selectionChanged.connect(self.display_reservations_for_date)
        layout.addWidget(self.calendar)

        self.setLayout(layout)

    def save_appointment(self):
        """Save the appointment details to the database."""
        name = self.name_input.text()
        ssn = self.ssn_input.text()
        address = self.address_input.text()
        phone = self.phone_input.text()
        date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        time = [btn.text() for btn in self.times if btn.isChecked()]

        if not time:
            QMessageBox.warning(self, "Input Error", "Please select a time slot!")
            return

        query = QSqlQuery()
        query.prepare(
            "INSERT INTO appointments (name, ssn, address, phone, date, time) VALUES (?, ?, ?, ?, ?, ?)"
        )
        query.addBindValue(name)
        query.addBindValue(ssn)
        query.addBindValue(address)
        query.addBindValue(phone)
        query.addBindValue(date)
        query.addBindValue(time[0])

        if not query.exec_():
            QMessageBox.critical(self, "Database Error", "Failed to save appointment!")
        else:
            QMessageBox.information(self, "Success", "Appointment saved successfully!")
            self.display_reservations_for_date()

    def view_appointment(self):
        """View the details of an appointment based on SSN."""
        ssn = self.ssn_input.text()
        query = QSqlQuery(
            f"SELECT name, address, phone, date, time FROM appointments WHERE ssn='{ssn}'"
        )
        if query.next():
            details = {
                "Name": query.value(0),
                "Address": query.value(1),
                "Phone": query.value(2),
                "Date": query.value(3),
                "Time": query.value(4),
            }
            message = "\n".join([f"{k}: {v}" for k, v in details.items()])
            QMessageBox.information(self, "Appointment Details", message)
        else:
            QMessageBox.warning(self, "Not Found", "No appointment found for this SSN!")

    def edit_appointment(self):
        """Edit the details of an existing appointment based on SSN."""
        ssn = self.ssn_input.text()
        name = self.name_input.text()
        address = self.address_input.text()
        phone = self.phone_input.text()
        date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        time = [btn.text() for btn in self.times if btn.isChecked()]

        if not time:
            QMessageBox.warning(self, "Input Error", "Please select a time slot!")
            return

        query = QSqlQuery()
        query.prepare(
            "UPDATE appointments SET name=?, address=?, phone=?, date=?, time=? WHERE ssn=?"
        )
        query.addBindValue(name)
        query.addBindValue(address)
        query.addBindValue(phone)
        query.addBindValue(date)
        query.addBindValue(time[0])
        query.addBindValue(ssn)

        if not query.exec_():
            QMessageBox.critical(self, "Database Error", "Failed to edit appointment!")
        else:
            QMessageBox.information(
                self, "Success", "Appointment updated successfully!"
            )
            self.display_reservations_for_date()

    def delete_appointment(self):
        """Delete an appointment based on SSN."""
        ssn = self.ssn_input.text()
        query = QSqlQuery()
        query.prepare("DELETE FROM appointments WHERE ssn=?")
        query.addBindValue(ssn)

        if not query.exec_():
            QMessageBox.critical(
                self, "Database Error", "Failed to delete appointment!"
            )
        else:
            QMessageBox.information(
                self, "Success", "Appointment deleted successfully!"
            )
            self.display_reservations_for_date()

    def display_reservations_for_date(self):
        """Fetch and display appointments for the selected date."""
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        query = QSqlQuery(
            f"SELECT name, time, ssn FROM appointments WHERE date='{selected_date}' ORDER BY time"
        )

        reservations = []
        while query.next():
            name = query.value(0)
            time = query.value(1)
            ssn = query.value(2)
            reservations.append(f"Name: {name}, Time: {time}, SSN: {ssn}")

        # Update the text area
        if reservations:
            self.reservations_display.setPlainText("\n".join(reservations))
        else:
            self.reservations_display.setPlainText(
                "No reservations for the selected date."
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppointmentsApp()
    window.show()
    sys.exit(app.exec_())
