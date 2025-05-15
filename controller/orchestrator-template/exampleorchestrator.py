"""
Example Orchestrator - Shows how to integrate caching
"""

import os
import sys
import json
import time
import argparse
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import requests
from datetime import datetime

# Import cache integration
from orchestrator_cache_integration import get_cache_integration

# This will be overwritten by the controller during build
ORCHESTRATOR_NAME = "Example Orchestrator"
CACHE_ENABLED = True

class ExampleOrchestrator:
    """
    Example orchestrator with caching integration.
    """
    
    def __init__(self, controller_url, orchestrator_id):
        """
        Initialize the example orchestrator.
        
        Args:
            controller_url: URL of the controller
            orchestrator_id: ID of this orchestrator
        """
        self.controller_url = controller_url
        self.orchestrator_id = orchestrator_id
        
        # Initialize cache integration
        self.cache_integration = get_cache_integration(
            orchestrator_name=ORCHESTRATOR_NAME,
            cache_dir="./cache",
            enabled=CACHE_ENABLED
        )
        
        # Wrap the LLM function with caching
        self.process_prompt = self.cache_integration.wrap_llm_function(self._process_prompt)
        
        # Initialize event loop for async operations
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Start heartbeat thread
        self.heartbeat_active = True
        self.heartbeat_thread = threading.Thread(target=self._send_heartbeat, daemon=True)
        self.heartbeat_thread.start()
    
    async def _process_prompt(self, prompt):
        """
        Process a prompt (without caching).
        This is the function that will be wrapped with caching.
        
        Args:
            prompt: The prompt to process
            
        Returns:
            Response object
        """
        # In a real application, this would call an actual LLM API
        # For demo purposes, we'll simulate a response
        await asyncio.sleep(1.5)  # Simulate API latency
        
        # Create a response object similar to what the cache adapter expects
        from types import SimpleNamespace
        return SimpleNamespace(
            response=f"This is a simulated response to: {prompt}",
            model_used="gpt-3.5-turbo-simulated",
            latency=1.5,
            cost=0.002,
            input_tokens=len(prompt.split()),
            output_tokens=20,
            selected_model="gpt-3.5-turbo-simulated"
        )
    
    def _send_heartbeat(self):
        """Send heartbeat to controller"""
        while self.heartbeat_active:
            try:
                # Get cache status
                cache_status = self.cache_integration.get_cache_status()
                
                payload = {
                    "id": self.orchestrator_id,
                    "name": ORCHESTRATOR_NAME,
                    "cache_enabled": cache_status["enabled"]
                }
                
                headers = {'Content-Type': 'application/json'}
                res = requests.post(f"{self.controller_url}/heartbeat", 
                                   json=payload, headers=headers, timeout=5)
                print(f"[Heartbeat] {res.status_code}")
                
            except Exception as e:
                print(f"[Heartbeat Failed] {e}")
            
            time.sleep(60)  # Send every minute
    
    def open_gui(self):
        """Open the orchestrator GUI"""
        # Create the main window
        root = tk.Tk()
        root.title(f"MoolAI {ORCHESTRATOR_NAME}")
        root.geometry("900x700")
        
        # Create a simple interface
        frame = ttk.Frame(root)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Add a button to open the cache GUI
        cache_button = ttk.Button(frame, text="Open Cache Manager", 
                                 command=self.cache_integration.open_cache_gui)
        cache_button.pack(pady=20)
        
        # Add a label with instructions
        instructions = ttk.Label(frame, text="This is an example orchestrator with caching integration.\n"
                                           "Click the button above to open the cache manager.")
        instructions.pack(pady=20)
        
        # Start the GUI
        root.mainloop()
    
    def stop(self):
        """Stop the orchestrator"""
        self.heartbeat_active = False

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Example Orchestrator with Caching")
    parser.add_argument('--controller', required=True, help='Controller base URL (e.g. http://<ip>:5050)')
    parser.add_argument('--interval', type=int, default=60, help='Heartbeat interval in seconds')
    parser.add_argument('--gui', action='store_true', help='Launch with GUI')
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_args()
    orchestrator_id = f"orch_{int(time.time())}"

    print(f"[INFO] Orchestrator: {ORCHESTRATOR_NAME}")
    print(f"[INFO] Controller: {args.controller}")
    print(f"[INFO] Interval: {args.interval}s")
    print(f"[INFO] Cache Enabled: {CACHE_ENABLED}")

    # Create orchestrator
    orchestrator = ExampleOrchestrator(args.controller, orchestrator_id)
    
    try:
        if args.gui:
            # Open GUI
            orchestrator.open_gui()
        else:
            # Run in headless mode
            print("Running in headless mode. Press Ctrl+C to exit.")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping orchestrator...")
    finally:
        orchestrator.stop()

if __name__ == '__main__':
    main()
