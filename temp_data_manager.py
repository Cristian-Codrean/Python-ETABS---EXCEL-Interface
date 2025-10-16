import json
import os
import sqlite3
from datetime import datetime
import etabs_api.operations as etabs_ops

# Import the new Excel operations
try:
    from excel.operations import create_beam_excel_file
except ImportError:
    # Fallback for testing
    def create_beam_excel_file(template_path, output_path, beam_groups_data):
        print(f"Mock: Would create Excel from {template_path} to {output_path}")
        print(f"Beam groups data: {beam_groups_data}")
        return output_path


class TempDataManager:
    def __init__(self):
        self.temp_file = "beam_selection_temp.json"
        self.db_file = "frames.db"
        self.data = {
            "timestamp": None,
            "scenario_a": {
                "beam_groups": [],
                "rezistente_type": None,
                "etaj": None,
                "selected_combinations_upper": [],
                "selected_combinations_lower": [],
                "button_states": {
                    "DCL": False, "DCM": False, "DCH": False,
                    "Secundare": False, "Dir X": False, "Dir Y": False
                }
            },
            "scenario_b": {
                "beam_groups": [],
                "rezistente_type": None,
                "etaj": None,
                "selected_combinations_upper": [],
                "selected_combinations_lower": [],
                "button_states": {
                    "DCL": False, "DCM": False, "DCH": False,
                    "Secundare": False, "Dir X": False, "Dir Y": False
                }
            }
        }

    def save_temp_data(self, scenario, beam_groups, app_state):
        """Salveaza datele temporare pentru un scenario"""
        self.data["timestamp"] = datetime.now().isoformat()

        scenario_data = self.data[f"scenario_{scenario.lower()}"]
        scenario_data["beam_groups"] = beam_groups
        scenario_data["rezistente_type"] = app_state["top_radio_state"]
        scenario_data["etaj"] = app_state.get("etaj")
        scenario_data["selected_combinations_upper"] = app_state["selected_combinations"][f"{scenario}_upper"]
        scenario_data["selected_combinations_lower"] = app_state["selected_combinations"][f"{scenario}_lower"]

        # Save button states for this scenario
        for button_key, state in app_state["button_states"].items():
            if button_key[0] == scenario:
                scenario_data["button_states"][button_key[1]] = state

        # Save to JSON file
        with open(self.temp_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

        print(f"Temp data saved for scenario {scenario}")

    def load_temp_data(self):
        """Incarca datele temporare din fisier"""
        if os.path.exists(self.temp_file):
            with open(self.temp_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            return self.data
        return None

    def get_beam_info(self, beam_name):
        """Extrage informatii detaliate despre o grinda"""
        try:
            # Basic info
            label, story = etabs_ops.get_label_and_story(beam_name)
            guid = etabs_ops.get_frame_guid(beam_name)
            section_name = etabs_ops.get_section_name(beam_name)

            # Geometry info
            joints_data, length = etabs_ops.get_joint_coordinations_names_length(beam_name)

            # Section properties
            prop_modifiers = etabs_ops.get_prop_modifiers(beam_name)
            end_releases = etabs_ops.get_end_releases(beam_name)
            end_offsets = etabs_ops.get_end_length_offsets(beam_name)

            # Additional properties
            insertion_point = etabs_ops.get_insertion_point(beam_name)
            local_axis = etabs_ops.get_local_axis_angle(beam_name)
            line_mass = etabs_ops.get_line_mass(beam_name)
            rebar_ratio = etabs_ops.get_rebar_ratio(beam_name)

            beam_info = {
                "UniqueName": beam_name,
                "Label": label,
                "Story": story,
                "GUID": guid,
                "Length": round(length, 3),
                "SectionName": section_name,
                "Joints": joints_data,
                "PropModifiers": prop_modifiers,
                "EndReleases": end_releases,
                "EndLengthOffsets": end_offsets,
                "InsertionPoint": insertion_point,
                "LocalAxisAngle": local_axis,
                "LineMass": line_mass,
                "RebarRatio": rebar_ratio
            }

            return beam_info

        except Exception as e:
            print(f"Error getting beam info for {beam_name}: {e}")
            return {
                "UniqueName": beam_name,
                "Label": "N/A",
                "Story": "N/A",
                "GUID": "N/A",
                "Length": 0,
                "SectionName": "N/A",
                "Joints": {},
                "PropModifiers": None,
                "EndReleases": None,
                "EndLengthOffsets": None,
                "InsertionPoint": None,
                "LocalAxisAngle": None,
                "LineMass": None,
                "RebarRatio": None
            }

    def create_detailed_database(self):
        """Creeaza baza de date detaliata pentru toate grinzile selectate"""
        temp_data = self.load_temp_data()
        if not temp_data:
            print("No temp data found!")
            return False

        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Create detailed table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS BeamGroups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scenario TEXT NOT NULL,
            group_number INTEGER NOT NULL,
            beam_order INTEGER NOT NULL,
            UniqueName TEXT NOT NULL,
            Label TEXT,
            Story TEXT,
            GUID TEXT,
            Length REAL,
            SectionName TEXT,
            Material TEXT,
            Joints TEXT,
            PropModifiers TEXT,
            EndReleases TEXT,
            EndLengthOffsets TEXT,
            InsertionPoint TEXT,
            LocalAxisAngle REAL,
            LineMass REAL,
            RebarRatio REAL,
            selection_timestamp TEXT
        )
        """)

        # Create scenario settings table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ScenarioSettings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scenario TEXT NOT NULL,
            rezistente_type TEXT,
            etaj TEXT,
            selected_combinations_upper TEXT,
            selected_combinations_lower TEXT,
            dcl_state BOOLEAN,
            dcm_state BOOLEAN,
            dch_state BOOLEAN,
            secundare_state BOOLEAN,
            dirx_state BOOLEAN,
            diry_state BOOLEAN,
            timestamp TEXT
        )
        """)

        # Clear existing data
        cursor.execute("DELETE FROM BeamGroups")
        cursor.execute("DELETE FROM ScenarioSettings")

        # Insert data for both scenarios
        for scenario in ['a', 'b']:
            scenario_key = f"scenario_{scenario}"
            scenario_data = temp_data.get(scenario_key, {})
            beam_groups = scenario_data.get("beam_groups", [])

            if beam_groups:
                # Insert scenario settings
                cursor.execute("""
                INSERT INTO ScenarioSettings (
                    scenario, rezistente_type, etaj, selected_combinations_upper,
                    selected_combinations_lower, dcl_state, dcm_state, dch_state,
                    secundare_state, dirx_state, diry_state, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    scenario.upper(),
                    scenario_data.get("rezistente_type"),
                    scenario_data.get("etaj"),
                    json.dumps(scenario_data.get("selected_combinations_upper", [])),
                    json.dumps(scenario_data.get("selected_combinations_lower", [])),
                    scenario_data.get("button_states", {}).get("DCL", False),
                    scenario_data.get("button_states", {}).get("DCM", False),
                    scenario_data.get("button_states", {}).get("DCH", False),
                    scenario_data.get("button_states", {}).get("Secundare", False),
                    scenario_data.get("button_states", {}).get("Dir X", False),
                    scenario_data.get("button_states", {}).get("Dir Y", False),
                    temp_data.get("timestamp")
                ))

                # Insert beam groups data
                for group_idx, group in enumerate(beam_groups, 1):
                    for beam_order, beam_name in enumerate(group, 1):
                        beam_info = self.get_beam_info(beam_name)

                        cursor.execute("""
                        INSERT INTO BeamGroups (
                            scenario, group_number, beam_order, UniqueName, Label, Story,
                            GUID, Length, SectionName, Material, Joints, PropModifiers,
                            EndReleases, EndLengthOffsets, InsertionPoint, LocalAxisAngle,
                            LineMass, RebarRatio, selection_timestamp
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            scenario.upper(),
                            group_idx,
                            beam_order,
                            beam_info["UniqueName"],
                            beam_info["Label"],
                            beam_info["Story"],
                            beam_info["GUID"],
                            beam_info["Length"],
                            beam_info["SectionName"],
                            "Concrete",
                            json.dumps(beam_info["Joints"]),
                            json.dumps(beam_info["PropModifiers"]),
                            json.dumps(beam_info["EndReleases"]),
                            json.dumps(beam_info["EndLengthOffsets"]),
                            json.dumps(beam_info["InsertionPoint"]),
                            beam_info["LocalAxisAngle"],
                            beam_info["LineMass"],
                            beam_info["RebarRatio"],
                            temp_data.get("timestamp")
                        ))

        conn.commit()

        # Print summary
        cursor.execute("SELECT COUNT(*) FROM BeamGroups")
        total_beams = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT scenario) FROM ScenarioSettings")
        total_scenarios = cursor.fetchone()[0]

        print(f"Database created successfully!")
        print(f"Total beams: {total_beams}")
        print(f"Total scenarios: {total_scenarios}")

        conn.close()
        return True

    def get_detailed_summary_data(self, app_state):
        """Returneaza datele detaliate pentru verificare"""
        temp_data = self.load_temp_data()
        if not temp_data:
            return None

        summary = {
            "timestamp": temp_data.get("timestamp"),
            "scenarios": {}
        }

        for scenario in ['a', 'b']:
            scenario_key = f"scenario_{scenario}"
            scenario_data = temp_data.get(scenario_key, {})
            beam_groups = scenario_data.get("beam_groups", [])

            if beam_groups:
                scenario_name = "Infrastructura" if scenario == 'a' else "Suprastructura"
                summary["scenarios"][scenario_name] = {
                    "group_count": len(beam_groups),
                    "total_beams": sum(len(group) for group in beam_groups),
                    "beam_groups": [],
                    "settings": {
                        "rezistente_type": scenario_data.get("rezistente_type"),
                        "etaj": scenario_data.get("etaj"),
                        "combinations_upper": scenario_data.get("selected_combinations_upper", []),
                        "combinations_lower": scenario_data.get("selected_combinations_lower", []),
                        "button_states": scenario_data.get("button_states", {})
                    }
                }

                # Add detailed beam info for each group
                for group_idx, group in enumerate(beam_groups, 1):
                    group_info = {
                        "group_number": group_idx,
                        "beams": []
                    }
                    for beam_name in group:
                        beam_info = self.get_beam_info(beam_name)
                        group_info["beams"].append({
                            "unique_name": beam_name,
                            "label": beam_info["Label"],
                            "story": beam_info["Story"],
                            "length": beam_info["Length"],
                            "section_name": beam_info["SectionName"],
                            "section_props": str(beam_info["PropModifiers"]),
                            "material": "Concrete"
                        })
                    summary["scenarios"][scenario_name]["beam_groups"].append(group_info)

        return summary

    def create_excel_file(self, result_folder, template_file):
        """Creeaza fisier Excel folosind functiile din excel/operations.py"""
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_filename = f"beam_analysis_{timestamp}.xlsx"
            excel_path = os.path.join(result_folder, excel_filename)

            # Load temp data for beam groups
            temp_data = self.load_temp_data()
            if not temp_data:
                print("No temp data found for Excel creation")
                return None

            # Prepare beam groups data for Excel function
            beam_groups_data = {}

            for scenario in ['a', 'b']:
                scenario_key = f"scenario_{scenario}"
                scenario_data = temp_data.get(scenario_key, {})
                beam_groups = scenario_data.get("beam_groups", [])

                if beam_groups:
                    scenario_name = "Infrastructura" if scenario == 'a' else "Suprastructura"
                    beam_groups_data[scenario_name] = {
                        'beam_groups': beam_groups,
                        'settings': {
                            'rezistente_type': scenario_data.get('rezistente_type'),
                            'etaj': scenario_data.get('etaj'),
                            'button_states': scenario_data.get('button_states', {})
                        }
                    }

            if not beam_groups_data:
                print("No beam groups data found for Excel creation")
                return None

            # Use the Excel function from excel/operations.py
            result = create_beam_excel_file(template_file, excel_path, beam_groups_data)

            if result:
                print(f"Excel file created successfully: {excel_path}")
                return excel_path
            else:
                print("Failed to create Excel file")
                return None

        except Exception as e:
            print(f"Error creating Excel file: {e}")
            return None