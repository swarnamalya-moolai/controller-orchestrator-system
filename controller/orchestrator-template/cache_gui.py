"""
Cache GUI - Simplified version with only prompt testing functionality
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from datetime import datetime

class CacheGUI:
    """
    Simplified GUI for prompt testing.
    """
    
    def __init__(self, root, orchestrator_name="Orchestrator"):
        """
        Initialize the cache GUI.
        
        Args:
            root: Tkinter root window
            orchestrator_name: Name of the orchestrator
        """
        self.root = root
        self.orchestrator_name = orchestrator_name
        self.root.title(f"MoolAI {orchestrator_name} - Prompt Testing")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Define colors
        self.orange = "#FF7700"
        self.dark_orange = "#CC5500"
        self.black = "#1E1E1E"
        self.dark_gray = "#2D2D2D"
        self.light_gray = "#3D3D3D"
        self.text_color = "#F0F0F0"
        
        # Set up styles
        self.style = ttk.Style()
        self.style.theme_use('default')
        
        # Configure styles
        self.style.configure('TFrame', background=self.black)
        self.style.configure('TLabel', background=self.black, foreground=self.text_color)
        self.style.configure('TButton', background=self.orange, foreground=self.black)
        self.style.configure('Header.TLabel', font=('Arial', 16, 'bold'), background=self.black, foreground=self.orange)
        
        self.style.map('TButton', 
            background=[('active', self.dark_orange), ('pressed', self.dark_orange)],
            foreground=[('active', self.black), ('pressed', self.black)])
        
        # Set root background
        self.root.configure(bg=self.black)
        
        # Create main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Setup the chat interface
        self._setup_chat_interface()
    
    def _setup_chat_interface(self):
        """Setup the chat interface for prompt testing"""
        # Header
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        header_label = ttk.Label(header_frame, text="Prompt Testing", style='Header.TLabel')
        header_label.pack(side=tk.LEFT, pady=10)
        
        # Chat history
        self.chat_history = scrolledtext.ScrolledText(self.main_frame, wrap=tk.WORD, 
                                                     bg=self.dark_gray, fg=self.text_color,
                                                     insertbackground=self.text_color)
        self.chat_history.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.chat_history.config(state=tk.DISABLED)
        
        # Input area
        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.prompt_input = scrolledtext.ScrolledText(input_frame, height=4, wrap=tk.WORD,
                                                     bg=self.light_gray, fg=self.text_color,
                                                     insertbackground=self.text_color)
        self.prompt_input.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 10))
        
        # Send button
        send_button = ttk.Button(input_frame, text="Send", command=self._send_prompt)
        send_button.pack(side=tk.RIGHT, padx=5)
        
        # Bind Enter key to send
        self.prompt_input.bind("<Control-Return>", lambda event: self._send_prompt())
    
    def _send_prompt(self):
        """Send a prompt and display the response"""
        prompt = self.prompt_input.get("1.0", tk.END).strip()
        if not prompt:
            return
        
        # Clear input
        self.prompt_input.delete("1.0", tk.END)
        
        # Display user message
        self._append_to_chat("You", prompt)
        
        # Process in background to keep UI responsive
        threading.Thread(target=self._process_prompt, args=(prompt,), daemon=True).start()
    
    def _process_prompt(self, prompt):
        """Process the prompt and get response"""
        try:
            # Simulate LLM processing
            start_time = time.time()
            
            # In a real application, this would call the actual LLM
            # For demo purposes, we'll simulate a response
            time.sleep(1.5)  # Simulate API latency
            response = f"This is a simulated response to: {prompt}"
            
            processing_time = time.time() - start_time
            response += f"\n\n[Generated in {processing_time:.2f}s]"
            
            # Display assistant message
            self.root.after(0, lambda: self._append_to_chat("Assistant", response))
            
        except Exception as e:
            error_msg = f"Error processing prompt: {str(e)}"
            self.root.after(0, lambda: self._append_to_chat("System", error_msg, error=True))
    
    def _append_to_chat(self, sender, message, error=False):
        """Append a message to the chat history"""
        self.chat_history.config(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Format based on sender
        if sender == "You":
            self.chat_history.insert(tk.END, f"\n[{timestamp}] You:\n", "user")
            self.chat_history.insert(tk.END, f"{message}\n\n", "user_msg")
        elif sender == "Assistant":
            self.chat_history.insert(tk.END, f"\n[{timestamp}] Assistant:\n", "assistant")
            self.chat_history.insert(tk.END, f"{message}\n\n", "assistant_msg")
        else:
            self.chat_history.insert(tk.END, f"\n[{timestamp}] {sender}:\n", "system")
            self.chat_history.insert(tk.END, f"{message}\n\n", "error" if error else "system_msg")
        
        # Configure tags
        self.chat_history.tag_config("user", foreground=self.orange, font=("Arial", 10, "bold"))
        self.chat_history.tag_config("user_msg", foreground=self.text_color)
        self.chat_history.tag_config("assistant", foreground=self.orange, font=("Arial", 10, "bold"))
        self.chat_history.tag_config("assistant_msg", foreground=self.text_color)
        self.chat_history.tag_config("system", foreground="#AAAAAA", font=("Arial", 9, "italic"))
        self.chat_history.tag_config("system_msg", foreground="#AAAAAA")
        self.chat_history.tag_config("error", foreground="#FF5555", font=("Arial", 9, "italic"))
        
        # Scroll to end
        self.chat_history.see(tk.END)
        self.chat_history.config(state=tk.DISABLED)
    
    def on_closing(self):
        """Handle window closing"""
        self.root.destroy()

# Function to create and run the GUI - KEEP THIS NAME FOR COMPATIBILITY
def run_cache_gui(orchestrator_name="Orchestrator"):
    """
    Create and run the cache GUI.
    
    Args:
        orchestrator_name: Name of the orchestrator
    """
    root = tk.Tk()
    app = CacheGUI(root, orchestrator_name)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

# Run the application if executed directly
if __name__ == "__main__":
    run_cache_gui("Prompt Testing")