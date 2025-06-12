import tkinter as tk
from tkinter import scrolledtext, messagebox
import random
import time
import datetime
import os


SCORES_FILE = "high_scores.txt"

# Theme colors
bg_color = "#F0F0F0"
fg_color = "#333333"
button_bg_main = "#36AEF4"
button_fg = "#FFFFFF"
entry_bg = "#FFFFFF"
entry_fg = "#000000"
label_bg = "#F0F0F0"
label_fg_title = "#2196F3"
label_fg_normal = "#555555"
exit_button_bg = "#F44336"
exit_button_fg = "#FFFFFF"
easy_color = "#81C784"
medium_color = "#FFB300"
extreme_color = "#E53935"
correct_char_color = "#4CAF50"
incorrect_char_color = "#F44336"

# Game state variables
current_sentence = ""
current_level = ""
game_running = False
timer_id = None
start_time = 0
user_name = ""
last_score_info = "N/A"
total_game_duration = 0  
time_elapsed = 0
total_typed_characters = 0
total_correct_characters = 0

# Widget references
root_window = None
main_frame = None
game_frame = None
scores_frame = None
results_frame = None
name_entry = None
sentence_display = None
user_input = None
timer_label = None
wpm_label = None
accuracy_label = None
last_score_label = None
user_name_var = None

# GAME FUNCTIONS 
def load_high_scores():
    """Load high scores from file."""
    scores = []
    if not os.path.exists(SCORES_FILE):
        return scores
    
    try:
        with open(SCORES_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 5:
                    scores.append({
                        'name': parts[0],
                        'score': int(parts[1]),
                        'wpm': float(parts[2]),
                        'accuracy': float(parts[3]),
                        'date': parts[4]
                    })
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load scores: {str(e)}")
    return scores

def save_high_score(score_data):
    """Save a score to the high scores file."""
    try:
        with open(SCORES_FILE, "a") as f:
            f.write(f"{score_data['name']},{score_data['score']},{score_data['wpm']:.2f},{score_data['accuracy']:.2f},{score_data['date']}\n")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save score: {str(e)}")

def get_random_sentence(level="medium"):
    """Get a random sentence based on difficulty level."""
    easy = [
        "The cat sat on the mat.",
        "I love to code in Python.",
        "The sun is shining today.",
        "Dogs are loyal animals.",
        "Practice makes perfect."
    ]
    
    medium = [
        "The quick brown fox jumps over the lazy dog.",
        "Python is a powerful programming language.",
        "Typing quickly and accurately takes practice.",
        "The early bird catches the worm.",
        "Learning new skills improves your brain."
    ]
    
    hard = [
        "Pneumonoultramicroscopicsilicovolcanoconiosis is a lung disease.",
        "The juxtaposition of ideas created cognitive dissonance.",
        "Quantum mechanics describes nature at atomic scales.",
        "Exponential growth appears in many natural processes.",
        "The antidisestablishmentarianism movement was political."
    ]
    
    if level == "easy":
        return random.choice(easy)
    elif level == "hard":
        return random.choice(hard)
    else:
        return random.choice(medium)

def calculate_wpm(chars_typed, seconds_elapsed):
    """Calculate words per minute (5 chars = 1 word)."""
    if seconds_elapsed <= 0:
        return 0.0
    words = chars_typed / 5
    minutes = seconds_elapsed / 60
    return words / minutes

def calculate_accuracy(correct_chars, total_chars):
    """Calculate typing accuracy percentage."""
    if total_chars <= 0:
        return 0.0
    return (correct_chars / total_chars) * 100

# GUI FUNCTIONS 
def clear_placeholder(event):
    """Clear the name entry placeholder text."""
    if user_name_var.get() == "Enter Your Name":
        user_name_var.set("")
        name_entry.config(fg=entry_fg)

def set_placeholder(event):
    """Set the name entry placeholder if empty."""
    if not user_name_var.get():
        user_name_var.set("Enter Your Name")
        name_entry.config(fg='grey')

def validate_name(text):
    """Validate name contains only letters and spaces."""
    if len(text) > 20:
        return False
    return all(c.isalpha() or c.isspace() for c in text)

def update_typing_feedback(event=None):
    """Update the visual feedback as user types."""
    global total_typed_characters, total_correct_characters
    
    if not game_running or not user_input.winfo_exists():
        return
    
    typed = user_input.get("1.0", tk.END).strip()
    sentence_display.config(state=tk.NORMAL)
    sentence_display.delete("1.0", tk.END)
    
    current_correct = 0
    for i, char in enumerate(current_sentence):
        if i < len(typed):
            if typed[i] == char:
                sentence_display.insert(tk.END, char, "correct")
                current_correct += 1
            else:
                sentence_display.insert(tk.END, char, "incorrect")
        else:
            sentence_display.insert(tk.END, char, "normal")
    
    sentence_display.config(state=tk.DISABLED)
    
    # Update stats
    time_elapsed = time.time() - start_time
    wpm = calculate_wpm(len(typed), time_elapsed)
    accuracy = calculate_accuracy(current_correct, len(typed)) if typed else 0
    
    wpm_label.config(text=f"WPM: {wpm:.2f}")
    accuracy_label.config(text=f"Accuracy: {accuracy:.2f}%")
    
    # Check if sentence completed
    if typed == current_sentence:
        total_typed_characters += len(current_sentence)
        total_correct_characters += len(current_sentence)
        next_sentence()

def next_sentence():
    """Load the next sentence for typing."""
    global current_sentence
    current_sentence = get_random_sentence(current_level)
    
    sentence_display.config(state=tk.NORMAL)
    sentence_display.delete("1.0", tk.END)
    sentence_display.insert(tk.END, current_sentence)
    sentence_display.config(state=tk.DISABLED)
    
    user_input.delete("1.0", tk.END)
    user_input.focus()

def update_timer():
    """Update the game timer display."""
    global timer_id, game_running, time_elapsed
    
    if not game_running:
        return
    
    time_elapsed = time.time() - start_time
    remaining = max(0, total_game_duration - time_elapsed)
    
    if remaining > 0:
        timer_label.config(text=f"Time Left: {int(remaining)}s")
        timer_id = root_window.after(1000, update_timer)
    else:
        game_running = False
        timer_label.config(text="Time's Up!", fg=incorrect_char_color)
        user_input.config(state=tk.DISABLED)
        end_game()

def start_game(level):
    """Start a new typing test game."""
    global current_level, current_sentence, game_running, start_time
    global total_typed_characters, total_correct_characters, total_game_duration
    global user_name, sentence_display, user_input, timer_label, wpm_label, accuracy_label
    
    # Set game duration based on difficulty
    if level == "easy":
        total_game_duration = 20  
    elif level == "medium":
        total_game_duration = 50  
    else:
        total_game_duration = 100  
    
    # Get user name
    user_name = user_name_var.get().strip()
    if not user_name or user_name == "Enter Your Name":
        messagebox.showwarning("Name Required", "Please enter your name before starting.")
        return
    
    # Reset game state
    current_level = level
    current_sentence = get_random_sentence(level)
    total_typed_characters = 0
    total_correct_characters = 0
    
    # Clear previous frames
    for widget in root_window.winfo_children():
        widget.destroy()
    
    # Create game UI
    game_frame = tk.Frame(root_window, bg=bg_color, padx=20, pady=20)
    game_frame.pack(expand=True, fill=tk.BOTH)
    
    # Sentence display
    tk.Label(game_frame, text=f"Type the following ({level} level):", 
             font=("Arial", 16), bg=label_bg, fg=label_fg_normal).pack(pady=10)
    
    sentence_display = scrolledtext.ScrolledText(game_frame, height=4, width=70,
                                                font=("Courier", 16), bg=entry_bg, fg=entry_fg)
    sentence_display.insert(tk.END, current_sentence)
    sentence_display.config(state=tk.DISABLED)
    sentence_display.pack(pady=10)
    
    # User input
    tk.Label(game_frame, text="Your typing:", font=("Arial", 16),
             bg=label_bg, fg=label_fg_normal).pack(pady=10)
    
    user_input = tk.Text(game_frame, height=4, width=70, font=("Courier", 16),
                        bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    user_input.pack(pady=10)
    user_input.focus()
    
    # Stats display
    stats_frame = tk.Frame(game_frame, bg=bg_color)
    stats_frame.pack(pady=10)
    
    timer_label = tk.Label(stats_frame, text=f"Time Left: {total_game_duration}s",
                          font=("Arial", 16), bg=label_bg, fg=label_fg_title)
    timer_label.pack(side=tk.LEFT, padx=20)
    
    wpm_label = tk.Label(stats_frame, text="WPM: 0.00", font=("Arial", 16),
                        bg=label_bg, fg=label_fg_normal)
    wpm_label.pack(side=tk.LEFT, padx=20)
    
    accuracy_label = tk.Label(stats_frame, text="Accuracy: 0.00%", font=("Arial", 16),
                            bg=label_bg, fg=label_fg_normal)
    accuracy_label.pack(side=tk.LEFT, padx=20)
    # Button controls
    button_frame = tk.Frame(game_frame, bg=bg_color)
    button_frame.pack(pady=20)
    tk.Button(button_frame, text="Restart", command=lambda: start_game(level),
             font=("Arial", 14), bg=button_bg_main, fg=button_fg).pack(side=tk.LEFT, padx=10)   
    tk.Button(button_frame, text="Main Menu", command=show_main_menu,
             font=("Arial", 14), bg=exit_button_bg, fg=exit_button_fg).pack(side=tk.RIGHT, padx=10)
    # Configure tags for coloring
    sentence_display.tag_config("correct", foreground=correct_char_color)
    sentence_display.tag_config("incorrect", foreground=incorrect_char_color)
    sentence_display.tag_config("normal", foreground=entry_fg)  
    # Set up event bindings
    user_input.bind("<KeyRelease>", update_typing_feedback)
      # Disable copy/paste
    for seq in ["<Control-c>", "<Control-v>", "<Control-x>"]:
        user_input.bind(seq, lambda e: "break")
    # Start game timer
    game_running = True
    start_time = time.time()
    update_timer()
def end_game():
    """Handle game ending and show results."""
    global last_score_info, user_name
    # Calculate final stats
    final_wpm = calculate_wpm(total_typed_characters, time_elapsed)
    final_accuracy = calculate_accuracy(total_correct_characters, total_typed_characters)
    score = int(final_wpm * (final_accuracy / 100))
    
    # Save score
    score_data = {
        'name': user_name,
        'score': score,
        'wpm': final_wpm,
        'accuracy': final_accuracy,
        'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    save_high_score(score_data)
    # Update last score display
    last_score_info = f"{user_name}: {score} (WPM: {final_wpm:.2f}, Acc: {final_accuracy:.2f}%)"   
    # Show results screen
    show_results(score_data)
def show_results(score_data):
    """Display the game results screen."""
    global results_frame   
    # Clear existing frames
    for widget in root_window.winfo_children():
        widget.destroy()    
    results_frame = tk.Frame(root_window, bg=bg_color, padx=20, pady=20)
    results_frame.pack(expand=True, fill=tk.BOTH)
    # Results header
    tk.Label(results_frame, text="Test Results", font=("Arial", 28, "bold"),
            bg=label_bg, fg=label_fg_title).pack(pady=20)  
    # Results details
    tk.Label(results_frame, text=f"Player: {score_data['name']}", 
            font=("Arial", 16), bg=label_bg, fg=label_fg_normal).pack(pady=5)
    
    tk.Label(results_frame, text=f"Time: {time_elapsed:.1f} seconds", 
            font=("Arial", 16), bg=label_bg, fg=label_fg_normal).pack(pady=5)
    
    tk.Label(results_frame, text=f"Words Per Minute: {score_data['wpm']:.2f}", 
            font=("Arial", 16), bg=label_bg, fg=label_fg_normal).pack(pady=5)
    
    tk.Label(results_frame, text=f"Accuracy: {score_data['accuracy']:.2f}%", 
            font=("Arial", 16), bg=label_bg, fg=label_fg_normal).pack(pady=5)
    
    tk.Label(results_frame, text=f"Score: {score_data['score']}", 
            font=("Arial", 20, "bold"), bg=label_bg, fg=label_fg_title).pack(pady=15)   
    # Action buttons
    button_frame = tk.Frame(results_frame, bg=bg_color)
    button_frame.pack(pady=20)
    
    tk.Button(button_frame, text="Play Again", command=lambda: start_game(current_level),
             font=("Arial", 14), bg=button_bg_main, fg=button_fg).pack(side=tk.LEFT, padx=10)
    
    tk.Button(button_frame, text="Main Menu", command=show_main_menu,
             font=("Arial", 14), bg=button_bg_main, fg=button_fg).pack(side=tk.LEFT, padx=10)
    
    tk.Button(button_frame, text="High Scores", command=show_high_scores,
             font=("Arial", 14), bg=button_bg_main, fg=button_fg).pack(side=tk.LEFT, padx=10)
    
    tk.Button(button_frame, text="Exit", command=root_window.quit,
             font=("Arial", 14), bg=exit_button_bg, fg=exit_button_fg).pack(side=tk.RIGHT, padx=10)
def show_high_scores():
    """Display the high scores screen."""
    global scores_frame
    # Clear existing frames
    for widget in root_window.winfo_children():
        widget.destroy()
    scores_frame = tk.Frame(root_window, bg=bg_color, padx=20, pady=20)
    scores_frame.pack(expand=True, fill=tk.BOTH)   
    # Header
    tk.Label(scores_frame, text="High Scores", font=("Arial", 28, "bold"),
            bg=label_bg, fg=label_fg_title).pack(pady=20) 
    # Get and sort scores
    scores = load_high_scores()
    scores_sorted = sorted(scores, key=lambda x: x['score'], reverse=True)[:10]
    # Display scores
    if not scores_sorted:
        tk.Label(scores_frame, text="No high scores yet!", font=("Arial", 16),
                bg=label_bg, fg=label_fg_normal).pack(pady=20)
    else:
        score_text = scrolledtext.ScrolledText(scores_frame, width=80, height=15,font=("Courier", 12), bg=entry_bg, fg=entry_fg)
        score_text.pack(pady=10)
        # Header
        header = "Rank  Name Score  WPM    Accuracy  Date\n"
        score_text.insert(tk.END, header)
        score_text.insert(tk.END, "-"*60 + "\n")
        # Add each score
        for i, score in enumerate(scores_sorted):
            line = f"{i+1:<5} {score['name'][:15]:<15} {score['score']:<6} {score['wpm']:<6.1f} {score['accuracy']:<8.1f} {score['date']}\n"
            score_text.insert(tk.END, line)        
        score_text.config(state=tk.DISABLED)    
    # Back button
    tk.Button(scores_frame, text="Back to Menu", command=show_main_menu,
             font=("Arial", 14), bg=button_bg_main, fg=button_fg).pack(pady=20)
def show_main_menu():
    """Display the main menu screen."""
    global main_frame, user_name_var, name_entry, last_score_label
    global game_running, timer_id
    # Stop any running game
    game_running = False
    if timer_id:
        root_window.after_cancel(timer_id)
        timer_id = None  
    # Clear existing frames
    for widget in root_window.winfo_children():
        widget.destroy()   
    # Create main menu
    main_frame = tk.Frame(root_window, bg=bg_color, padx=20, pady=20)
    main_frame.pack(expand=True, fill=tk.BOTH)   
    # Title
    tk.Label(main_frame, text="Typing Master", font=("Arial", 36, "bold"),
            bg=label_bg, fg=label_fg_title).pack(pady=30)   
    # Name entry
    user_name_var = tk.StringVar(value=user_name if user_name else "Enter Your Name")
    vcmd = (root_window.register(validate_name), '%P')
    name_entry = tk.Entry(main_frame, textvariable=user_name_var, font=("Arial", 14),
                         validate="key", validatecommand=vcmd, bg=entry_bg, 
                         fg=entry_fg if user_name else 'grey')
    name_entry.pack(pady=10)
    name_entry.bind("<FocusIn>", clear_placeholder)
    name_entry.bind("<FocusOut>", set_placeholder)
    name_entry.focus()   
    # Last score
    last_score_label = tk.Label(main_frame, text=f"Last Score: {last_score_info}",
                              font=("Arial", 12), bg=label_bg, fg=label_fg_normal)
    last_score_label.pack(pady=5)
    # Difficulty buttons
    tk.Label(main_frame, text="Select Difficulty:", font=("Arial", 16),
            bg=label_bg, fg=label_fg_normal).pack(pady=15)
    button_width = 15   
    tk.Button(main_frame, text="Easy", command=lambda: start_game("easy"),
             font=("Arial", 14), bg=easy_color, fg=button_fg, width=button_width).pack(pady=5)  
    tk.Button(main_frame, text="Medium", command=lambda: start_game("medium"),
             font=("Arial", 14), bg=medium_color, fg=button_fg, width=button_width).pack(pady=5)   
    tk.Button(main_frame, text="Hard", command=lambda: start_game("hard"),
             font=("Arial", 14), bg=extreme_color, fg=button_fg, width=button_width).pack(pady=5)
    # Other buttons
    tk.Button(main_frame, text="High Scores", command=show_high_scores,
             font=("Arial", 14), bg=button_bg_main, fg=button_fg, width=button_width).pack(pady=10)   
    tk.Button(main_frame, text="Exit", command=root_window.quit,
             font=("Arial", 14), bg=exit_button_bg, fg=exit_button_fg, width=button_width).pack(pady=5)
#MAIN PROGRAM 
if __name__ == "__main__":
    # Create main window
    root_window = tk.Tk()
    root_window.title("Typing Master")
    root_window.geometry("900x700")
    root_window.configure(bg=bg_color)
    
    # Center window
    root_window.update_idletasks()
    width = root_window.winfo_width()
    height = root_window.winfo_height()
    x = (root_window.winfo_screenwidth() // 2) - (width // 2)
    y = (root_window.winfo_screenheight() // 2) - (height // 2)
    root_window.geometry(f"{width}x{height}+{x}+{y}")
    show_main_menu()
    root_window.mainloop()