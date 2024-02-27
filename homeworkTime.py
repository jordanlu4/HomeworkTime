import tkinter as tk
from tkinter import messagebox
from threading import Thread
import time
import json
import sqlite3
from datetime import datetime


#pyinstaller --onefile --windowed .\homeworkTime.py

class TimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Homework Time")
        root.geometry("1000x600")
        self.init_db()
        self.root.configure(bg='#96799e')  


        # Timer state
        self.running = False
        self.start_time = None  # Track start time of the current timing session
        self.saved_elapsed_time = 0  # Save elapsed time during pauses

        # Timer display
        self.timer_label = tk.Label(root, text="00:00:00", font=("Helvetica", 48), bg='#96799e')
        self.timer_label.pack()

        # Start button
        self.start_button = tk.Button(root, text="Start", command=self.start_timer, bg='#96799e')
        self.start_button.place(x=50, y=100, width=175, height=50)

        # Pause button
        self.pause_button = tk.Button(root, text="Pause", command=self.pause_timer, bg='#96799e')
        self.pause_button.place(x=410, y=100, width=175, height=50)

        # Clear button
        self.log_button = tk.Button(root, text="Log", command=self.log_timer, bg='#96799e')
        self.log_button.place(x=770, y=100, width=175, height=50)

        self.weekly_summary_button = tk.Button(root, text="Weekly Summary", command=lambda: self.display_summary('weekly'), bg='#96799e')
        self.weekly_summary_button.place(x=50, y=250, width=175, height=50)

        self.monthly_summary_button = tk.Button(root, text="Monthly Summary", command=lambda: self.display_summary('monthly'), bg='#96799e')
        self.monthly_summary_button.place(x=50, y=350, width=175, height=50)

        self.yearly_summary_button = tk.Button(root, text="Yearly Summary", command=lambda: self.display_summary('yearly'), bg='#96799e')
        self.yearly_summary_button.place(x=50, y=450, width=175, height=50)


    def update_timer(self):
        """Update the timer display with milliseconds."""
        self.start_time = time.time() - self.saved_elapsed_time 
        while self.running:
            now = time.time()
            elapsed = now - self.start_time
            self.time_elapsed = elapsed


            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            milliseconds = int((seconds - int(seconds)) * 1000)
            seconds = int(seconds)

            time_str = f"{int(hours):02d}:{int(minutes):02d}:{seconds:02d}.{milliseconds:03d}"
            self.timer_label.config(text=time_str)

            time.sleep(0.01)  

    def start_timer(self):
        """Start or resume the timer."""
        if not self.running:
            self.running = True
            self.timer_thread = Thread(target=self.update_timer)
            self.timer_thread.start()

    def pause_timer(self):
        """Pause the timer."""
        self.running = False
        self.saved_elapsed_time += time.time() - self.start_time

    def log_timer(self):
        """Clear the timer and log the session."""
        if self.running or self.saved_elapsed_time > 0:
            end_time = time.time()
            start_time = end_time - self.saved_elapsed_time  
            duration = self.saved_elapsed_time

            if duration > 0:
                self.log_study_session(start_time, end_time, duration)
            self.running = False
            self.saved_elapsed_time = 0
            self.time_elapsed = 0
            self.timer_label.config(text="00:00:00")

        
    def init_db(self):
        self.conn = sqlite3.connect('homework_timer.db')
        self.cur = self.conn.cursor()
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS study_log (
                id INTEGER PRIMARY KEY,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration INTEGER
            )
        ''')
        self.conn.commit()


    def log_study_session(self, start_time, end_time, duration):
        self.cur.execute('''
            INSERT INTO study_log (start_time, end_time, duration)
            VALUES (?, ?, ?)
        ''', (start_time, end_time, duration))
        self.conn.commit()


    def get_summary(self, period='weekly'):
        if period == 'weekly':
            query = '''
                SELECT date(start_time, 'weekday 0', '-7 days') as week_start, SUM(duration)
                FROM study_log
                WHERE start_time >= datetime('now', 'start of day', '-7 days')
                GROUP BY week_start
                ORDER BY week_start
            '''
        elif period == 'monthly':
            query = '''
                SELECT strftime('%Y-%W', start_time) as week, SUM(duration)
                FROM study_log
                WHERE start_time >= datetime('now', 'start of day', '-1 month')
                GROUP BY week
                ORDER BY week
            '''
        elif period == 'yearly':
            query = '''
                SELECT strftime('%Y-%m', start_time) as month, SUM(duration)
                FROM study_log
                WHERE start_time >= datetime('now', 'start of day', '-1 year')
                GROUP BY month
                ORDER BY month
            '''

        self.cur.execute(query)
        return self.cur.fetchall()
    
    def format_duration(self, duration):
        seconds = int(duration) % 60
        minutes = (int(duration) // 60) % 60
        hours = (int(duration) // 3600) % 24
        days = int(duration) // 86400

        return f"{days:02d}d:{hours:02d}h:{minutes:02d}m:{seconds:02d}s"

    def log_study_session(self, start_time, end_time, duration):
        # Convert epoch to formatted strings if necessary
        start_time_str = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
        end_time_str = datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')

        self.cur.execute('''
            INSERT INTO study_log (start_time, end_time, duration)
            VALUES (?, ?, ?)
        ''', (start_time_str, end_time_str, duration))
        self.conn.commit()

    def clear_view(self):
        for widget in self.root.winfo_children():
            widget.destroy()


    def display_summary(self, period):
        self.clear_view()  
        summary_data = self.get_summary(period)
    
        for i, row in enumerate(summary_data, start=1):
            tk.Label(self.root, text=f"Time: {row[0]}, Duration: {self.format_duration(row[1])}", bg='#96799e', font=("Helvetica", 12)).pack(pady=(5, 0))
        

        self.back_button = tk.Button(self.root, text="← Back", command=self.reset_view, bg='#96799e')
        self.back_button.place(x=10, y=10) 

        

    def reset_view(self):
        self.clear_view() 
        self.timer_label = tk.Label(self.root, text="00:00:00", font=("Helvetica", 48), bg='#96799e')
        self.timer_label.pack()
        self.start_button = tk.Button(self.root, text="Start", command=self.start_timer, bg='#96799e')
        self.start_button.place(x=50, y=100, width=175, height=50)
        self.pause_button = tk.Button(self.root, text="Pause", command=self.pause_timer, bg='#96799e')
        self.pause_button.place(x=410, y=100, width=175, height=50)
        self.log_button = tk.Button(self.root, text="Log", command=self.log_timer, bg='#96799e')
        self.log_button.place(x=770, y=100, width=175, height=50)

        self.weekly_summary_button = tk.Button(self.root, text="Weekly Summary", command=lambda: self.display_summary('weekly'), bg='#96799e')
        self.weekly_summary_button.place(x=50, y=250, width=175, height=50)
        self.monthly_summary_button = tk.Button(self.root, text="Monthly Summary", command=lambda: self.display_summary('monthly'), bg='#96799e')
        self.monthly_summary_button.place(x=50, y=350, width=175, height=50)
        self.yearly_summary_button = tk.Button(self.root, text="Yearly Summary", command=lambda: self.display_summary('yearly'), bg='#96799e')
        self.yearly_summary_button.place(x=50, y=450, width=175, height=50)





def main():
    root = tk.Tk()
    app = TimerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

