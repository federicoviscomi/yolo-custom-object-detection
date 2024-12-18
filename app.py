import os
import pandas

from glob import glob
from xml.etree import ElementTree as et
from xml.etree.ElementTree import Element, ElementTree
from typing import List
from shutil import rmtree, copyfile


def label_encoding(label: str) -> int:
    labels = {
        "arrow": 0,
        "bus lane": 1,
        "diamond": 2,
        "crossing": 3,
        "slow": 4,
        "right arrow": 5,
        "left arrow": 6,
    }
    return labels[label]


def find_text_required(root: Element, path: str) -> str:
    element: Element = find_required(root, path)
    if (text := element.text) is not None:
        return text
    raise ValueError("text is None")


def find_required(root: Element, path: str) -> Element:
    if (element := root.find(path)) is not None:
        return element
    raise ValueError("cannot find path " + path)


def delete_dir_if_exists(path: str) -> None:
    directory_path = "/data/generated"
    if os.path.exists(directory_path):
        rmtree(directory_path)
    os.makedirs(directory_path)


def save_bulk(destination_directory: str, group_by_obj: pandas.core.groupby.generic.DataFrameGroupBy) -> None:
    filename_series: pandas.Series = pandas.Series(list(group_by_obj.groups.keys()))
    filenames: List[str] = filename_series.to_list()
    for filename in filenames:
        save_data(filename, destination_directory, group_by_obj)


def save_data(filename: str, destination_directory: str,
              group_by_obj: pandas.core.groupby.generic.DataFrameGroupBy) -> None:
    source = "/data/images/{filename}".format(filename=filename)
    destination = ("{destination_directory}/{filename}"
                   .format(destination_directory=destination_directory, filename=filename))
    basename = os.path.splitext(filename)[0]
    text_filename = ("{destination_directory}/{basename}.txt"
                     .format(destination_directory=destination_directory, basename=basename))
    copyfile(source, destination)
    group_by_obj.get_group(filename).set_index("filename").to_csv(text_filename, index=False, header=False)
    print(source, destination, text_filename)


xml_list: List[str] = glob("/data/annotations/train/*.xml")
parsed_all = []
for annotation_file in xml_list:
    tree: ElementTree = et.parse(annotation_file)
    root: Element = tree.getroot()
    file_name: str = find_text_required(root, "filename")
    width: int = int(find_text_required(root, "size/width"))
    height: int = int(find_text_required(root, "size/height"))
    objects: List[Element] = root.findall("object")
    for obj in objects:
        annotation_name = find_text_required(obj, "name")
        bndbox = find_required(obj, "bndbox")
        xmin = int(find_text_required(bndbox, "xmin"))
        xmax = int(find_text_required(bndbox, "xmax"))
        ymin = int(find_text_required(bndbox, "ymin"))
        ymax = int(find_text_required(bndbox, "ymax"))
        parsed_all.append(
            [file_name, width, height, annotation_name, xmin, xmax, ymin, ymax]
        )

df = pandas.DataFrame(
    parsed_all,
    columns=["filename", "width", "height", "name", "xmin", "xmax", "ymin", "ymax"],
)

df["center_x"] = ((df["xmax"] + df["xmin"]) / 2) / df["width"]
df["center_y"] = ((df["ymax"] + df["ymin"]) / 2) / df["height"]
df["w"] = (df["xmax"] - df["xmin"]) / df["width"]
df["h"] = (df["ymax"] - df["ymin"]) / df["height"]

# df.info()
# print("df.head()", df.head())
# print("df.shape", df.shape)
# print('df["name"].value_counts()', df["name"].value_counts())

images = df["filename"].unique()
img_df = pandas.DataFrame(images, columns=["filename"])
img_train = tuple(img_df.sample(frac=0.8)["filename"])
img_test = tuple(img_df.query(f"filename not in {img_train}")["filename"])
# print("there are ", len(images), " images in total")
# print("there are ", len(img_train), " images in training")
# print("there are ", len(img_test), " images in test")

train_df = df.query(f"filename in {img_train}")
test_df = df.query(f"filename in {img_test}")
# print("test_df.head()", test_df.head())
# print("train_df.head()", train_df.head())
# print(df["name"].unique())

train_df["id"] = train_df["name"].apply(label_encoding)
test_df["id"] = test_df["name"].apply(label_encoding)

# with pandas.option_context('display.max_columns', None):
#     print(test_df.head())
# with pandas.option_context('display.max_columns', None):
#     print(train_df.head())

train_folder = "/data/generated/train"
test_folder = "/data/generated/test"
delete_dir_if_exists("/data/generated")
os.makedirs(train_folder)
os.makedirs(test_folder)

cols = ["filename", "id", "center_x", "center_y", "w", "h"]
groupby_obj_train: pandas.core.groupby.DataFrameGroupBy = train_df[cols].groupby(
    "filename"
)
groupby_obj_test: pandas.core.groupby.DataFrameGroupBy = test_df[cols].groupby("filename")
# print(groupby_obj_train.head())
# print(groupby_obj_test.head())

save_bulk('/data/generated/train', groupby_obj_train)
save_bulk('/data/generated/test', groupby_obj_test)

