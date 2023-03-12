import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem, QInputDialog, QMessageBox, QTabWidget,
)
import sqlite3
import math


def expected_score(player_rating, opponent_rating):
    return 1 / (1 + math.pow(10, (opponent_rating - player_rating) / 400))


class RatingSystemApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up initial ratings for players
        self.initial_ratings = {}

        # Set up K-factor for the rating system
        self.K_FACTOR = 32

        # Set up database connection
        self.conn = sqlite3.connect("rating_system.db")
        self.cur = self.conn.cursor()
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS score (id INTEGER PRIMARY KEY, player1 TEXT, player2 TEXT, player1_score "
            "INTEGER, player2_score INTEGER, player1_weightage FLOAT, player2_weightage FLOAT, match_id INT) ",
        )
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS player (id INTEGER PRIMARY KEY, name TEXT, matches_played INTEGER, "
            "wins INTEGER, losses INTEGER, rating INTEGER) "
        )
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS match (id INTEGER PRIMARY KEY, name TEXT, weightage FLOAT)"
        )

        # self.cur.execute(
        #     "INSERT INTO player (name, matches_played, wins, losses, rating) VALUES ('Alex', 0, 0, 0, 1000),('Troy', "
        #     "0, 0, 0, 1000),('Jeff', 0, 0, 0, 1000),('Jack', 0, 0, 0, 1000),('Qadeer', 0, 0, 0, 1000)"
        # )
        self.conn.commit()

        # Set up UI
        self.setWindowTitle("Table Tennis Rating System")
        self.setFixedSize(1000, 600)

        # Create central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create a button to add a new player
        self.add_player_button = QPushButton("Add Player", self)
        self.add_player_button.setGeometry(500, 0, 100, 30)
        self.add_player_button.clicked.connect(self.add_player)

        # Create a button to rename the selected player
        self.rename_player_button = QPushButton("Rename Player", self)
        self.rename_player_button.setGeometry(600, 0, 120, 30)
        self.rename_player_button.clicked.connect(self.rename_player)

        # Create player input widgets
        player1_layout = QHBoxLayout()
        player1_label = QLabel("Player 1:")
        player1_input = QLineEdit()
        player1_layout.addWidget(player1_label)
        player1_layout.addWidget(player1_input)

        player2_layout = QHBoxLayout()
        player2_label = QLabel("Player 2:")
        player2_input = QLineEdit()
        player2_layout.addWidget(player2_label)
        player2_layout.addWidget(player2_input)

        # Create score input widgets
        score_layout = QHBoxLayout()
        player1_score_label = QLabel("Player 1 Score:")
        player1_score_input = QLineEdit()
        player1_score_input.setValidator(QIntValidator())
        player2_score_label = QLabel("Player 2 Score:")
        player2_score_input = QLineEdit()
        player2_score_input.setValidator(QIntValidator())
        score_layout.addWidget(player1_score_label)
        score_layout.addWidget(player1_score_input)
        score_layout.addWidget(player2_score_label)
        score_layout.addWidget(player2_score_input)

        # Create button to record score
        record_score_button = QPushButton("Record Score")
        record_score_button.clicked.connect(
            lambda: self.record_score(
                player1_input.text(),
                player2_input.text(),
                int(player1_score_input.text()),
                int(player2_score_input.text()),
            )
        )

        # Create table to display score history
        score_history_table = QTableWidget()
        score_history_table.setColumnCount(5)
        score_history_table.setHorizontalHeaderLabels(
            ["ID", "Player 1", "Player 2", "Player 1 Score", "Player 2 Score", "Match ID", "Player 1 Weightage",
             "Player 2 Weightage"]
        )

        # Create table to display players
        player_data_table = QTableWidget()
        player_data_table.setColumnCount(6)
        player_data_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Matches_played", "Wins", "Losses", "Rating"]
        )

        # Create table to display players
        match_data_table = QTableWidget()
        match_data_table.setColumnCount(3)
        match_data_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Weightage"]
        )
        self.load_players(player_data_table)
        self.load_score_history(score_history_table)
        self.load_matches(match_data_table)
        self.load_player_ratings()

        # Add widgets to main layout
        main_layout.addLayout(player1_layout)
        main_layout.addLayout(player2_layout)
        main_layout.addLayout(score_layout)
        main_layout.addWidget(record_score_button)

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()
        self.tabs.resize(300, 200)

        # Add tabs
        self.tabs.addTab(self.tab1, "Players")
        self.tabs.addTab(self.tab2, "Match_Scores")
        self.tabs.addTab(self.tab3, "Match_Info")
        self.tabs.addTab(self.tab4, "Options")

        # Create Players tab
        self.tab1.layout = QVBoxLayout(self)
        self.tab1.layout.addWidget(player_data_table)
        self.tab1.setLayout(self.tab1.layout)

        # Create Scores tab
        self.tab2.layout = QVBoxLayout(self)
        self.tab2.layout.addWidget(score_history_table)
        self.tab2.setLayout(self.tab2.layout)

        # Create Matches tab
        self.tab3.layout = QVBoxLayout(self)
        self.tab3.layout.addWidget(match_data_table)
        self.tab3.setLayout(self.tab3.layout)

        # Create Options tab
        self.tab4.layout = QVBoxLayout(self)
        self.tab4.layout.addWidget(self.add_player_button)
        self.tab4.layout.addWidget(self.rename_player_button)
        self.tab4.setLayout(self.tab4.layout)

        # Add tabs to widget
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def rename_player(self):
        # Get the selected player from the player list
        selected_row = self.player_list.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Error", "Please select a player to rename.")
            return
        player = self.player_list.item(selected_row).text()

        # Get the new name for the player from the user
        new_name, ok = QInputDialog.getText(self, "Rename Player", f"Enter a new name for {player}:")

        # If the user clicked "OK", rename the player in the database and refresh the player list
        if ok:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE players SET name = ? WHERE name = ?", (new_name, player))
                conn.commit()
            self.refresh_player_list()

    def add_player(self):
        # Get the name of the new player from the user
        new_player, ok = QInputDialog.getText(self, "Add New Player", "Enter the name of the new player:")

        # If the user clicked "OK", add the new player to the database and refresh the player list
        if ok:
            self.cur.execute("INSERT INTO player (name, matches_played, wins, losses, rating) VALUES (?, ?, ?, ?, ?)",
                             (new_player, 0, 0, 0, 1000))
            self.conn.commit()
            self.load_player_ratings()

    def load_player_ratings(self):
        self.cur.execute("SELECT * FROM player ORDER BY player.rating")
        players = self.cur.fetchall()
        for player in players:
            self.initial_ratings[player[1]] = player[5]

    def update_ratings(self, player1, player2, player1_wins):
        # Get current ratings for both players
        player1_rating = self.initial_ratings[player1]
        player2_rating = self.initial_ratings[player2]

        # Calculate expected score for each player
        player1_expected_score = expected_score(player1_rating, player2_rating)
        player2_expected_score = expected_score(player2_rating, player1_rating)

        # Calculate actual score for each player
        if player1_wins:
            player1_actual_score = 1
            player2_actual_score = 0
            self.cur.execute(
                "UPDATE player SET matches_played = matches_played + 1, wins = wins + 1 "
                " WHERE name = ?",
                [player1])
            self.cur.execute(
                "UPDATE player SET matches_played = matches_played + 1, losses = losses + "
                "1 WHERE name = ?",
                [player2])
        else:
            player1_actual_score = 0
            player2_actual_score = 1
            self.cur.execute(
                "UPDATE player SET matches_played = matches_played + 1, losses = losses + "
                "1 WHERE name = ?", [player1])
            self.cur.execute(
                "UPDATE player SET matches_played = matches_played + 1, wins = wins + 1 "
                "WHERE name = ?", [player2])

        # Update ratings for both players
        player1_new_rating = player1_rating + self.K_FACTOR * (
                player1_actual_score - player1_expected_score
        )
        player2_new_rating = player2_rating + self.K_FACTOR * (
                player2_actual_score - player2_expected_score
        )

        # Update initial_ratings dict with new ratings
        self.initial_ratings[player1] = int(player1_new_rating)
        self.initial_ratings[player2] = int(player2_new_rating)
        self.cur.execute(
            "UPDATE player SET rating = ?1 WHERE player.name = ?2",
            (int(player1_new_rating), player1))
        self.cur.execute(
            "UPDATE player SET rating = ?1 WHERE player.name = ?2",
            (int(player2_new_rating), player2))

        self.conn.commit()

    def record_score(self, player1, player2, player1_score, player2_score):
        # Determine winner and update ratings
        if player1_score > player2_score:
            self.update_ratings(player1, player2, True)
        else:
            self.update_ratings(player1, player2, False)

        # Insert score into database
        self.cur.execute(
            "INSERT INTO score (player1, player2, player1_score, player2_score) VALUES (?, ?, ?, ?)",
            (player1, player2, player1_score, player2_score),
        )
        self.conn.commit()

        # Reload score history table
        score_history_table = self.centralWidget().findChild(QTableWidget)
        self.load_score_history(score_history_table)

    def load_score_history(self, score_history_table):
        # Clear existing data from table
        score_history_table.setRowCount(0)

        # Retrieve score from database
        self.cur.execute("SELECT * FROM score")
        score = self.cur.fetchall()

        # Populate table with score
        for score in score:
            row_position = score_history_table.rowCount()
            score_history_table.insertRow(row_position)
            for column_position, data in enumerate(score):
                score_history_table.setItem(
                    row_position, column_position, QTableWidgetItem(str(data))
                )

    def load_players(self, player_data_table):
        # Clear existing data from table
        player_data_table.setRowCount(0)

        # Retrieve players from database
        self.cur.execute("SELECT * FROM player ORDER BY player.rating DESC")
        players = self.cur.fetchall()

        for player in players:
            row_position = player_data_table.rowCount()
            player_data_table.insertRow(row_position)
            for column_position, data in enumerate(player):
                player_data_table.setItem(
                    row_position, column_position, QTableWidgetItem(str(data))
                )

    def load_matches(self, match_data_table):
        # Clear existing data from table
        match_data_table.setRowCount(0)

        # Retrieve players from database
        self.cur.execute("SELECT * FROM match")
        players = self.cur.fetchall()

        for player in players:
            row_position = match_data_table.rowCount()
            match_data_table.insertRow(row_position)
            for column_position, data in enumerate(player):
                match_data_table.setItem(
                    row_position, column_position, QTableWidgetItem(str(data))
                )

    def closeEvent(self, event):
        # Close database connection when application is closed
        self.conn.close()
        event.accept()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == "__main__":
    sys.excepthook = except_hook
    app = QApplication(sys.argv)
    rating_system_app = RatingSystemApp()
    rating_system_app.show()
    sys.exit(app.exec_())
