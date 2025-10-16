import tkinter as tk
from tkinter import ttk, filedialog
import sys
import os

# ==================== FIX IMPORTS ====================
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    import etabs_api.operations

    print("ETABS API imported successfully")
except ImportError as e:
    print(f"ETABS API import warning: {e}")


    # Fallback for testing
    class MockOperations:
        @staticmethod
        def get_story_names(): return ["B1", "P1", "P2", "P3", "P4", "P5"]

        @staticmethod
        def get_comb_names(): return [f"Combo{i}" for i in range(1, 21)]

        @staticmethod
        def get_selected_frames_live():
            import random
            frames = ["Frame1", "Frame2", "Frame3", "Frame4", "Frame5"]
            return random.sample(frames, random.randint(1, 3))

        @staticmethod
        def clear_frame_selection(): return True

        @staticmethod
        def hide_specific_frames(frame_list):
            print(f"Mock: Hiding frames {frame_list}")
            return True


    etabs_api.operations = MockOperations()

# FIX: Import widgets correctly - try different methods
try:
    from .widgets import ScenarioFrame, FileSelectionFrame, ControlButtons, SelectionConfirmationDialog, \
        SimpleSummaryPopup
    from .temp_data_manager import TempDataManager
except ImportError:
    try:
        from widgets import ScenarioFrame, FileSelectionFrame, ControlButtons, SelectionConfirmationDialog, \
            SimpleSummaryPopup
        from temp_data_manager import TempDataManager
    except ImportError:
        try:
            sys.path.insert(0, current_dir)
            from widgets import ScenarioFrame, FileSelectionFrame, ControlButtons, SelectionConfirmationDialog, \
                SimpleSummaryPopup
            from temp_data_manager import TempDataManager
        except ImportError as e:
            print(f"Failed to import widgets: {e}")
            sys.exit(1)


class DesignApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Design Comparison Tool")
        self.root.resizable(True, True)

        # Initialize temp data manager
        self.temp_manager = TempDataManager()

        # Test ETABS connection
        try:
            stories = etabs_api.operations.get_story_names()
            print(f"Connected to ETABS. Stories: {stories}")
        except Exception as e:
            print(f"ETABS connection test failed: {e}")
            print("Running in mock mode with sample data")

        # ==================== STATE TRACKING ====================
        self.button_states = {
            ("A", "DCL"): False, ("A", "DCM"): False, ("A", "DCH"): False,
            ("A", "Secundare"): False, ("A", "Dir X"): False, ("A", "Dir Y"): False,
            ("B", "DCL"): False, ("B", "DCM"): False, ("B", "DCH"): False,
            ("B", "Secundare"): False, ("B", "Dir X"): False, ("B", "Dir Y"): False,
        }
        self.top_radio_state = "Normale"
        self.selected_combinations = {
            "A_upper": [], "A_lower": [], "B_upper": [], "B_lower": []
        }
        self.etaj_value = None

        # ==================== BEAM SELECTION TRACKING ====================
        self.beam_selection_active = False
        self.current_beam_group = []
        self.all_beam_groups_a = []  # For Infrastructura
        self.all_beam_groups_b = []  # For Suprastructura
        self.current_scenario = None
        self.tracking_id = None

        # ==================== MAIN CONTAINER ====================
        container = ttk.Frame(self.root)
        container.pack(expand=True, fill="both")

        # --- Top switch ---
        switches_frame = ttk.Frame(container)
        switches_frame.pack(pady=10)
        self.rezistente_var = tk.StringVar(value="Normale")
        switch1 = ttk.Frame(switches_frame)
        switch1.pack()
        tk.Radiobutton(switch1, text="Rezistente Normale", variable=self.rezistente_var, value="Normale",
                       command=self.update_top_radio_state).pack(side="left", padx=20)
        tk.Radiobutton(switch1, text="Rezistente Medii", variable=self.rezistente_var, value="Medii",
                       command=self.update_top_radio_state).pack(side="left", padx=20)

        # --- Etaj dropdown ---
        ttk.Label(container, text="Etaj:").pack()
        self.story_var = tk.StringVar()
        self.story_dropdown = ttk.Combobox(container, textvariable=self.story_var, state="readonly")
        self.story_dropdown['values'] = [i for i in etabs_api.operations.get_story_names()]
        self.story_dropdown.pack(pady=5)
        self.story_dropdown.bind('<<ComboboxSelected>>', self.update_etaj_value)

        # --- Scenario frames container ---
        frame_scenarios = ttk.Frame(container)
        frame_scenarios.pack()

        # ==================== SCENARIO FRAMES ====================
        self.scenario_a = ScenarioFrame(
            parent=frame_scenarios,
            scenario_name="Infrastructura",
            scenario_id="A",
            button_states=self.button_states,
            button_command=self.set_variant,
            clear_command=self.clear_scenario_a,
            action_command=lambda: self.start_beam_selection("A")
        )
        self.scenario_a.frame.grid(row=0, column=0, padx=20, pady=10, sticky="n")

        self.scenario_b = ScenarioFrame(
            parent=frame_scenarios,
            scenario_name="Suprastructura",
            scenario_id="B",
            button_states=self.button_states,
            button_command=self.set_variant,
            clear_command=self.clear_scenario_b,
            action_command=lambda: self.start_beam_selection("B")
        )
        self.scenario_b.frame.grid(row=0, column=1, padx=20, pady=10, sticky="n")

        # Fill listboxes
        self.fill_listbox(self.scenario_a.list_upper)
        self.fill_listbox(self.scenario_a.list_lower)
        self.fill_listbox(self.scenario_b.list_upper)
        self.fill_listbox(self.scenario_b.list_lower)

        # ==================== CONTROL BUTTONS ====================
        self.control_buttons = ControlButtons(
            parent=container,
            check_command=self.check_selection,
            clear_command=self.unselect_all
        )
        self.control_buttons.pack(pady=5)

        # ==================== FILE SELECTION ====================
        self.file_frame = FileSelectionFrame(
            parent=container,
            browse_default_command=self.browse_default_file,
            browse_result_command=self.browse_result_folder
        )
        self.file_frame.pack(pady=10, fill=tk.X, padx=20)

        # ==================== CREATE EXCEL BUTTON ====================
        ttk.Button(container, text="Create Excel", command=self.create_excel, width=40).pack(
            pady=20, ipadx=20, ipady=10
        )

    # ==================== UPDATED UNSELECT ALL FUNCTION ====================
    def unselect_all(self):
        """Clear ALL data from BOTH scenarios"""
        print("Clear All Selection pressed - clearing ALL temporary data from BOTH scenarios")

        # Clear all beam groups from BOTH scenarios
        self.all_beam_groups_a = []
        self.all_beam_groups_b = []
        self.current_beam_group = []

        # Clear temporary file
        if os.path.exists("beam_selection_temp.json"):
            os.remove("beam_selection_temp.json")
            print("Temporary data file cleared")

        # Clear database file
        if os.path.exists("frames.db"):
            os.remove("frames.db")
            print("Database file cleared")

        # Clear ALL selections in GUI from BOTH scenarios
        self.clear_scenario_a()
        self.clear_scenario_b()

        # Reset button states for BOTH scenarios
        for key in list(self.button_states.keys()):
            self.button_states[key] = False

        # Reset top radio state
        self.rezistente_var.set("Normale")
        self.top_radio_state = "Normale"

        # Reset etaj
        self.story_var.set("")
        self.etaj_value = None

        # Reset selected combinations for BOTH scenarios
        self.selected_combinations = {
            "A_upper": [], "A_lower": [], "B_upper": [], "B_lower": []
        }

        # Clear ETABS selection
        etabs_api.operations.clear_frame_selection()

        # Update button appearances for BOTH scenarios
        self.update_scenario_buttons("A")
        self.update_scenario_buttons("B")

        print("ALL temporary data cleared from BOTH scenarios. Ready to start new beam selection.")

    def update_scenario_buttons(self, scenario):
        """Update button appearances for a scenario"""
        scenario_obj = self.scenario_a if scenario == "A" else self.scenario_b
        buttons = scenario_obj.variant_buttons

        for variant, btn in buttons.items():
            state = self.button_states.get((scenario, variant), False)
            if variant in ["DCL", "DCM", "DCH", "Secundare"]:
                btn.config(relief="sunken" if state else "raised",
                           background="lightblue" if state else "SystemButtonFace")
            else:  # Dir X / Dir Y
                btn.config(relief="sunken" if state else "raised",
                           background="lightgreen" if state else "SystemButtonFace")

    # ==================== UPDATED CHECK SELECTION FUNCTION ====================
    def check_selection(self):
        """Show simple table summary of all selected beams"""
        print("Verificare Date Grinzi pressed")
        current_state = self.get_current_state()
        print(current_state)

        # Get detailed beam information
        summary_data = self.temp_manager.get_detailed_summary_data(current_state)
        if summary_data and summary_data.get("scenarios"):
            SimpleSummaryPopup(self.root, summary_data)
        else:
            print("No beam data available for verification")

    # ==================== REST OF THE CODE REMAINS THE SAME ====================
    # ... (all other functions remain exactly the same as in the previous version)

    def update_etaj_value(self, event=None):
        """Update etaj value when dropdown changes"""
        self.etaj_value = self.story_var.get()
        print(f"Etaj selected: {self.etaj_value}")

    def start_beam_selection(self, scenario):
        """Start beam selection process for the given scenario"""
        if self.beam_selection_active:
            print("Beam selection is already active!")
            return

        self.current_scenario = scenario
        self.beam_selection_active = True
        self.current_beam_group = []

        # Clear any previous selection in ETABS
        etabs_api.operations.clear_frame_selection()

        print(f"Started beam selection for {scenario}")
        print("Please select beams in ETABS...")

        # Show confirmation dialog
        self.show_selection_confirmation(scenario, is_first_group=True)

        # Start tracking beam selections in background
        self.start_tracking()

    def start_tracking(self):
        """Start tracking beam selections"""
        if self.beam_selection_active:
            self.track_beam_selections()

    def track_beam_selections(self):
        """Track beam selections in ETABS in real-time"""
        if not self.beam_selection_active:
            return

        try:
            # Get currently selected frames from ETABS (no limit now)
            selected_frames = etabs_api.operations.get_selected_frames_live()

            # Update current group with all selected frames
            self.current_beam_group = selected_frames.copy()

            if selected_frames:
                print(f"Currently selected beams ({len(selected_frames)}): {selected_frames}")

            # Continue tracking
            self.tracking_id = self.root.after(500, self.track_beam_selections)

        except Exception as e:
            print(f"Error tracking beams: {e}")
            self.tracking_id = self.root.after(500, self.track_beam_selections)

    def stop_tracking(self):
        """Stop the beam selection tracking"""
        if self.tracking_id:
            self.root.after_cancel(self.tracking_id)
            self.tracking_id = None

    def stop_beam_selection(self):
        """Stop the beam selection process completely"""
        self.beam_selection_active = False
        self.stop_tracking()
        print("Beam selection stopped")

    def confirm_and_continue(self):
        """Confirm current group and continue with next group"""
        if self.current_beam_group:
            # Save current group to the appropriate scenario
            if self.current_scenario == "A":
                self.all_beam_groups_a.append(self.current_beam_group.copy())
                current_groups = self.all_beam_groups_a
            else:
                self.all_beam_groups_b.append(self.current_beam_group.copy())
                current_groups = self.all_beam_groups_b

            print(
                f"Group {len(current_groups)} confirmed for scenario {self.current_scenario}: {self.current_beam_group}")

            # Save to temp file
            app_state = self.get_current_state()
            self.temp_manager.save_temp_data(
                self.current_scenario,
                current_groups,
                app_state
            )

            # Hide beams
            success = etabs_api.operations.hide_specific_frames(self.current_beam_group)
            if success:
                print("Beams hidden successfully in ETABS")
            else:
                print("Hiding method failed")

            # Clear selection for next group
            etabs_api.operations.clear_frame_selection()
            self.current_beam_group = []

            print("Ready for next beam group selection...")
            return True
        else:
            print("No beams selected in current group!")
            return False

    def confirm_and_stop(self):
        """Confirm current group and stop selection"""
        if self.current_beam_group:
            # Save current group
            if self.current_scenario == "A":
                self.all_beam_groups_a.append(self.current_beam_group.copy())
                current_groups = self.all_beam_groups_a
            else:
                self.all_beam_groups_b.append(self.current_beam_group.copy())
                current_groups = self.all_beam_groups_b

            print(f"Final group confirmed for scenario {self.current_scenario}")

            # Save to temp file
            app_state = self.get_current_state()
            self.temp_manager.save_temp_data(
                self.current_scenario,
                current_groups,
                app_state
            )

            # Hide beams
            etabs_api.operations.hide_specific_frames(self.current_beam_group)

        # Clear selection and stop
        etabs_api.operations.clear_frame_selection()
        self.stop_beam_selection()
        return True

    def cancel_selection(self):
        """Cancel current selection without saving"""
        print("Selection canceled")

        # Clear selection in ETABS
        etabs_api.operations.clear_frame_selection()
        self.current_beam_group = []
        self.stop_beam_selection()
        return True

    def create_excel(self):
        """Create database and then generate Excel file using excel/operations.py"""
        print("Create Excel triggered")

        # First create the database
        success = self.temp_manager.create_detailed_database()
        if not success:
            print("Failed to create database - cannot create Excel")
            return

        # Get result folder path
        result_folder = self.file_frame.result_folder_var.get()
        if not result_folder:
            print("Please select a result folder first")
            return

        # Get default file path for template
        default_file = self.file_frame.default_file_var.get()
        if not default_file:
            print("Please select a default Excel template file first")
            return

        # Generate Excel file using the new function
        try:
            excel_path = self.temp_manager.create_excel_file(result_folder, default_file)
            if excel_path:
                print(f"Excel file created successfully: {excel_path}")
            else:
                print("Failed to create Excel file")
        except Exception as e:
            print(f"Error creating Excel file: {e}")

    def show_selection_confirmation(self, scenario, is_first_group=False):
        """Show confirmation dialog for beam selection"""
        scenario_name = "Infrastructura" if scenario == "A" else "Suprastructura"

        self.confirmation_dialog = SelectionConfirmationDialog(
            parent=self.root,
            scenario_name=scenario_name,
            confirm_continue_callback=self.handle_confirm_continue,
            confirm_stop_callback=self.handle_confirm_stop,
            cancel_callback=self.handle_cancel,
            is_first_group=is_first_group
        )

    def handle_confirm_continue(self):
        """Handle 'Confirm and Continue' button press"""
        print("Confirm and Continue pressed")
        if self.confirm_and_continue():
            if self.confirmation_dialog:
                group_count = len(self.all_beam_groups_a if self.current_scenario == "A" else self.all_beam_groups_b)
                self.confirmation_dialog.update_message(
                    f"Grupul {group_count} confirmat!\n"
                    f"Selectati urmatorul grup de grinzi in ETABS..."
                )
        else:
            if self.confirmation_dialog:
                self.confirmation_dialog.update_message(
                    "EROARE: Nici o grinda selectata!\n"
                    "Selectati grinzi in ETABS inainte de confirmare."
                )

    def handle_confirm_stop(self):
        """Handle 'Confirm and Stop' button press"""
        print("Confirm and Stop pressed")
        if self.confirm_and_stop():
            if self.confirmation_dialog:
                self.confirmation_dialog.close_dialog()

    def handle_cancel(self):
        """Handle 'Cancel' button press"""
        print("Cancel pressed")
        if self.cancel_selection():
            if self.confirmation_dialog:
                self.confirmation_dialog.close_dialog()

    def fill_listbox(self, listbox):
        """Fill given listbox with design combinations"""
        for i in etabs_api.operations.get_comb_names():
            listbox.insert(tk.END, f"{i}")

    def set_variant(self, scenario, variant):
        """
        Handles variant button presses with proper unselect behavior
        """
        scenario_obj = self.scenario_a if scenario == "A" else self.scenario_b
        buttons = scenario_obj.variant_buttons
        states = self.button_states

        if variant in ["DCL", "DCM", "DCH"]:
            # Pressing DCL/DCM/DCH
            for v in ["DCL", "DCM", "DCH"]:
                pressed = (v == variant)
                buttons[v].config(relief="sunken" if pressed else "raised",
                                  background="lightblue" if pressed else "SystemButtonFace")
                states[(scenario, v)] = pressed
            # Unselect Secundare automatically
            buttons["Secundare"].config(relief="raised", background="SystemButtonFace")
            states[(scenario, "Secundare")] = False

        elif variant == "Secundare":
            # Secundare clears DCL/DCM/DCH and Dir X/Y
            for v in ["DCL", "DCM", "DCH", "Secundare"]:
                pressed = (v == "Secundare")
                buttons[v].config(relief="sunken" if pressed else "raised",
                                  background="lightblue" if pressed else "SystemButtonFace")
                states[(scenario, v)] = pressed
            # Clear Dir buttons
            for dir_btn in ["Dir X", "Dir Y"]:
                buttons[dir_btn].config(relief="raised", background="SystemButtonFace")
                states[(scenario, dir_btn)] = False

        else:  # Dir X / Dir Y
            other = "Dir X" if variant == "Dir Y" else "Dir Y"
            if states[(scenario, "Secundare")]:
                # Clear Dir buttons if Secundare active
                for dir_btn in ["Dir X", "Dir Y"]:
                    buttons[dir_btn].config(relief="raised", background="SystemButtonFace")
                    states[(scenario, dir_btn)] = False
            else:
                # Toggle current button, make sure only one Dir button is pressed
                buttons[variant].config(relief="sunken", background="lightgreen")
                buttons[other].config(relief="raised", background="SystemButtonFace")
                states[(scenario, variant)] = True
                states[(scenario, other)] = False

    def update_top_radio_state(self):
        self.top_radio_state = self.rezistente_var.get()

    def update_selected_combinations(self):
        self.selected_combinations["A_upper"] = [self.scenario_a.list_upper.get(i) for i in
                                                 self.scenario_a.list_upper.curselection()]
        self.selected_combinations["A_lower"] = [self.scenario_a.list_lower.get(i) for i in
                                                 self.scenario_a.list_lower.curselection()]
        self.selected_combinations["B_upper"] = [self.scenario_b.list_upper.get(i) for i in
                                                 self.scenario_b.list_upper.curselection()]
        self.selected_combinations["B_lower"] = [self.scenario_b.list_lower.get(i) for i in
                                                 self.scenario_b.list_lower.curselection()]

    def get_current_state(self):
        """Return a full snapshot of all states"""
        self.update_top_radio_state()
        self.update_selected_combinations()
        return {
            "button_states": self.button_states.copy(),
            "top_radio_state": self.top_radio_state,
            "selected_combinations": self.selected_combinations.copy(),
            "etaj": self.etaj_value,
            "beam_groups_a": self.all_beam_groups_a.copy(),
            "beam_groups_b": self.all_beam_groups_b.copy()
        }

    def clear_scenario_a(self):
        """Unselect only scenario A selections"""
        self.scenario_a.list_upper.selection_clear(0, tk.END)
        self.scenario_a.list_lower.selection_clear(0, tk.END)
        self.update_selected_combinations()

    def clear_scenario_b(self):
        """Unselect only scenario B selections"""
        self.scenario_b.list_upper.selection_clear(0, tk.END)
        self.scenario_b.list_lower.selection_clear(0, tk.END)
        self.update_selected_combinations()

    def browse_default_file(self):
        filename = filedialog.askopenfilename(title="Select Default File",
                                              filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
        if filename:
            self.file_frame.default_file_var.set(filename)

    def browse_result_folder(self):
        folder = filedialog.askdirectory(title="Select Result Folder")
        if folder:
            self.file_frame.result_folder_var.set(folder)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = DesignApp()
    app.run()