import sqlite3
import json
from etabs_api.operations import *
import os

def create_database(frame_list):
    """Creaza baza de date pentru elementele de tip frame (UniqueName) dintr-o lista."""

    # Delete existing file if it exists
    # if os.path.exists("frames.db"):
    #     os.remove("frames.db")
    #Connect to (or create) the database file
    conn = sqlite3.connect("frames.db")
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS Frames")

    #Create table with placeholders for all frame properties
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Frames (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        UniqueName TEXT NOT NULL,
        Label TEXT,
        GUID TEXT,
        Story TEXT,
        Joint_i TEXT,  --JSON: {"name":"","x":0,"y":0,"z":0]}
        Joint_j TEXT,  --JSON: {"name":"","x":0,"y":0,"z":0]}
        Length REAL,
        SectionName TEXT,
        PropModifiers TEXT,  -- JSON: {"Area":0,"As2":0,"As3":0,"Torsion":0,"I22":0,"I33":0,"Mass":0,"Weigh":0}
        EndReleases_i TEXT,  --JSON: "i":{"Axial":None,"Shear2":None,"Shear3":None,"Torsion":None,"Moment22":None,"Moment33":None}
        EndReleases_j TEXT,  --JSON: "j":{"Axial":None,"Shear2":None,"Shear3":None,"Torsion":None,"Moment22":None,"Moment33":None}
        EndLengthOffsets TEXT,  --JSON:{"i":0,"j":0,"RigidZoneFactor":0}
        InsertionPoint TEXT,
        OutputStations TEXT,    --JSON: {"OutputStationsBy":"-","Number":0}
        LocalAxisAngle REAL,    --In lucru
        Springs TEXT,    --In lucru
        LineMass REAL,
        TCLimits TEXT,    --JSON: {"Tension":None,"Compression":None}    --In lucru
        Spandrel TEXT,
        MaterialOverwrites TEXT,
        RebarRatio REAL,
        AutoMesh TEXT,    --In lucru
        Groups TEXT    --In lucru
    )
    """)

    for name in frame_list:
        cursor.execute("""
        INSERT INTO Frames (
            UniqueName, Label, GUID
        ) VALUES (?, ?, ?)
        """, (
            name,
            get_label_and_story(name)[0],
            get_frame_guid(name),
            # get_story(frame_name),
            # json.dumps(get_geometry(frame_name)),
            # json.dumps(get_assignments(frame_name)),
            # json.dumps(get_loads(frame_name)),
            # json.dumps(get_design(frame_name)),
            # json.dumps(get_design_overwrites(frame_name)),
            # json.dumps(get_indirect_assignments(frame_name)),
            # json.dumps(get_column_assignments(frame_name)),
            # json.dumps(get_design_forces(frame_name)),
            # json.dumps(get_column_mrd(frame_name)),
            # json.dumps(get_beam_rotations(frame_name))
        ))
    # for frame_name in frame_list:
    #     cursor.execute("""
    #     INSERT INTO Frames (
    #         UniqueName, Label, GUID, Story, Joint_i, Joint_j, Length, SectionName,
    #         PropModifiers, EndReleases_i, EndReleases_j, EndLengthOffsets, InsertionPoint, OutputStations,
    #         LocalAxisAngle, Springs, LineMass, TCLimits, Spandrel, MaterialOverwrites, RebarRatio, AutoMesh, Groups
    #     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    #     """, (
    #         frame_name,
    #         get_label_and_story(frame_name)[0],
    #         get_frame_guid(frame_name),
    #         get_story(frame_name),
    #         json.dumps(get_geometry(frame_name)),
    #         json.dumps(get_assignments(frame_name)),
    #         json.dumps(get_loads(frame_name)),
    #         json.dumps(get_design(frame_name)),
    #         json.dumps(get_design_overwrites(frame_name)),
    #         json.dumps(get_indirect_assignments(frame_name)),
    #         json.dumps(get_column_assignments(frame_name)),
    #         json.dumps(get_design_forces(frame_name)),
    #         json.dumps(get_column_mrd(frame_name)),
    #         json.dumps(get_beam_rotations(frame_name))
    #     ))

    #Commit changes
    conn.commit()

    #Optionally display inserted records
    cursor.execute("SELECT UniqueName, Label, Guid FROM Frames")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

    #Close connection
    conn.close()


# Example usage
if __name__ == "__main__":
    frame_names = ["pula","10","12"]
    create_database(frame_names)
