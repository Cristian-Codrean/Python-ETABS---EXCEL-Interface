def connect_to_etabs():
    import os
    import sys
    import comtypes.client

    # full path to the model
    APIPath = R'C:\Users\Cristian\Desktop\CSI API\Aplicatii\Aplicatie Nr 2.3\Aplicatie Nr 2.3\Modele ETABS'
    if not os.path.exists(APIPath):
        try:
            os.makedirs(APIPath)
        except OSError:
            pass
    ModelPath = APIPath + os.sep + 'Model 1'

    # create API helper object
    try:
        helper = comtypes.client.CreateObject('ETABSv1.Helper')
        helper = helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)
    except (OSError, comtypes.COMError) as e:
        print(f"Failed to create ETABS helper: {e}")
        return None

    # attach to a running instance of ETABS
    try:
        # get the active ETABS object
        myETABSObject = helper.GetObject("CSI.ETABS.API.ETABSObject")
        if myETABSObject is None:
            print("No running ETABS instance found. Please start ETABS first.")
            return None

        # create SapModel object
        SapModel = myETABSObject.SapModel
        print("Successfully connected to ETABS")
        return SapModel

    except (OSError, comtypes.COMError, AttributeError) as e:
        print(f"Failed to connect to ETABS: {e}")
        print("Please make sure ETABS is running")
        return None