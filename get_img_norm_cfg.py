from torch.utils.data import Dataset, DataLoader
from torch import Tensor
from tqdm import tqdm
from dataset.rgbt import RGBT

#
# class MyDataset(Dataset):
#     def __init__(self, image_list):
#         assert isinstance(image_list, list)
#         self.image_list = image_list
#
#     def __getitem__(self, index):
#         path = base + img_dir + self.image_list[index]
#         image = Image.open(path).convert("RGB")
#         img_arr = np.asarray(image, dtype=np.float32)
#         assert img_arr.dtype == np.float32
#         return img_arr
#
#     def __len__(self):
#         return len(self.image_list)

dataset = RGBT(root='D:\\Project_repository\\RGBT_multi_dataset\\DATASET_ROOT', online=False,
                   supplementary_rgb_num=0, image_set='all')

loader = DataLoader(
    dataset,
    batch_size=30,
    num_workers=0,
    shuffle=False
)

mean = Tensor([0, 0, 0])
std = Tensor([0, 0, 0])
n_samples = 0
for data in tqdm(loader):
    annot, thermal, rgb = data
    batch_samples = thermal.size(0)
    data2 = thermal.view(-1, 3)
    mean += data2.mean(0)
    std += data2.std(0)
    n_samples += 1


mean /= n_samples
std /= n_samples

print(f'img_norm_cfg = dict(\nmean={mean.tolist()},\nstd={std.tolist()},\nto_rgb=True\n)')