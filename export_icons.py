import os, json, re
from PIL import Image

def safe_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '', name).strip()

def load_bounded_boxes(jsonpath):
        if not jsonpath:
            return
        if not os.path.isfile(jsonpath):
            print(f"JSON file not found: {jsonpath}")
            return
        with open(jsonpath, 'r') as f:
            data = json.load(f)
            bbox_list = []
            for entry in data["DETAILS"]:
                bbox = [int(x) for x in entry["SearchBBOX"]]
                expandedbbox = [int(x) for x in entry["ExpandedBBOX"]]
                id = entry["ID"]
                name = safe_filename(entry["DESCRIPTION"])
                bbox_list.append([id,name,expandedbbox])
            return bbox_list

def crop_images(foldername, export_folder, jsonpath, imagepath):
    cropped_savepath = os.path.join(export_folder, foldername)
    if not os.path.exists(cropped_savepath):
        os.makedirs(cropped_savepath)
    loadimage = Image.open(imagepath)
    bbox_list = load_bounded_boxes(jsonpath)
    for id, name, bbox in bbox_list:
        x1, y1, x2, y2 = bbox
        croppedimage = loadimage.crop((x1, y1, x2, y2))
        if name == "" or name is None:
            name = id
        croppedimage.save(os.path.join(cropped_savepath, f"{name}.png"))


