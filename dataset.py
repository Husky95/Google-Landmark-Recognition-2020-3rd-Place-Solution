import os
import cv2
import numpy as np
import pandas as pd
import albumentations
import torch
from torch.utils.data import Dataset


class LandmarkDataset(Dataset):
    def __init__(self, csv, split, mode, transform=None):

        self.csv = csv.reset_index()
        self.split = split
        self.mode = mode
        self.transform = transform

    def __len__(self):
        return self.csv.shape[0]

    def __getitem__(self, index):
        row = self.csv.iloc[index]
        #print(row.filepath)
        image = cv2.imread(row.filepath)[:,:,::-1]

        if self.transform is not None:
            res = self.transform(image=image)
            image = res['image'].astype(np.float32)
        else:
            image = image.astype(np.float32)

        image = image.transpose(2, 0, 1)
        if self.mode == 'test':
            return torch.tensor(image)
        else:
            return torch.tensor(image), torch.tensor(row.individual_id)


def get_transforms(image_size):

    transforms_train = albumentations.Compose([
        #albumentations.HorizontalFlip(p=0.5),
        albumentations.ImageCompression(quality_lower=99, quality_upper=100),
        albumentations.ShiftScaleRotate(shift_limit=0.2, scale_limit=0.2, rotate_limit=10, border_mode=0, p=0.7),
        albumentations.Resize(image_size, image_size),
        albumentations.Cutout(max_h_size=int(image_size * 0.4), max_w_size=int(image_size * 0.4), num_holes=1, p=0.5),
        albumentations.Normalize()
    ])

    transforms_val = albumentations.Compose([
        albumentations.Resize(image_size, image_size),
        albumentations.Normalize()
    ])

    return transforms_train, transforms_val


def get_df(kernel_type, data_dir, train_step):

    #data_dir = '/kaggle/input/dolphin/train_images/'
    print(data_dir)
    df = pd.read_csv('train_0.csv')

    if train_step == 0:
      df_train = pd.read_csv('train.csv')
    else:
      cls_81313 = df.individual_id.unique()
      df_train = pd.read_csv('train.csv').set_index('individual_id').loc[cls_81313].reset_index()
        
    df_train['filepath'] = df_train['image'].apply(lambda x: os.path.join(data_dir, f'{x}'))
    df = df_train.merge(df, on=['image','individual_id'], how='left')

    landmark_id2idx = {landmark_id: idx for idx, landmark_id in enumerate(sorted(df['individual_id'].unique()))}
    idx2landmark_id = {idx: landmark_id for idx, landmark_id in enumerate(sorted(df['individual_id'].unique()))}
    df['individual_id'] = df['individual_id'].map(landmark_id2idx)

    out_dim = df.individual_id.nunique()
    print(out_dim)
    print(df)
      
    return df, out_dim
