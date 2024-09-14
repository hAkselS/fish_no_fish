# https://www.youtube.com/watch?v=qC4yEiJOJtM
# Use this video to write a script ^ 
# https://github.com/sovit-123/fasterrcnn-pytorch-training-pipeline
# Reference this as well ^
# https://github.com/harshatejas/pytorch_custom_object_detection/tree/main
# And this 
# https://brsoff.github.io/tutorials/beginner/finetuning_torchvision_models_tutorial.html

'''
Spec: this script is used to feature extract from restnet 50 using a custom dataset. 
The dataset consists of about 30 images hand annoted by yours truly in label studio. 
There is a train.json file associated with the dataset that contains the bounding box
and class information. The dataset is mostly defined in 'create_dataset.py' and imported
into this script. The purpose of this script is to remove the head from the dataset, 
replace with a custom head containing 3 classes [fish, bait_arm, background] and 
train the new head with a small amount of data .
feature extact = remove the classification layer and retrain a new one. 
'''

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time 

# 6:32 - list of all imports 
import torch 
import torchvision 
from torchvision.models.detection import FasterRCNN_ResNet50_FPN_Weights
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor 
from torch.utils.data import DataLoader # Used to translate my dataset to torch 
import torch.nn as nn 
import torch.optim as optim
#from torchvision import transforms as T 

import create_dataset as mydata     # Helper functions by Aks

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(f'device = {device}')

# Select an object detection model
custom_model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights=FasterRCNN_ResNet50_FPN_Weights.DEFAULT)

num_classes = 3  # fish, bait_arm, background
in_features = custom_model.roi_heads.box_predictor.cls_score.in_features

# Create the new box predictor with custom number of classes
custom_model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

# Pull in your dataset
mydataset = mydata.MyFishDataset()

# Collate function to handle varying sizes of bboxes and labels
def collate_fn(batch):
    #images = [item[0] for item in batch]
    #images = [item[0].float() / 255.0 for item in batch]  # Convert to float and normalize to [0, 1]
    images = [item[0][:3].float() / 255.0 for item in batch] # Convert to float, normalize [0, 1], and remove extra channel


    targets = []
    for item in batch:
        labels = torch.tensor(item[1], dtype=torch.int64)
        bboxes = torch.tensor(item[2], dtype=torch.float32)
        targets.append({"boxes": bboxes, "labels": labels})
    return images, targets

# Use the collate_fn in your DataLoader
train_dataloader = DataLoader(mydataset, batch_size=4, shuffle=False, collate_fn=collate_fn)

# Display image with bounding boxes and labels
def display_image_with_boxes(dataloader, idx, label_dict): # idx ranges from 0, batch-1 
    '''
    Displays an image with bbox from the first batch. 
    Only displays from range 0 to batch - 1. 
    '''
    images, targets = next(iter(dataloader))
    # Display the first image with its bounding boxes and labels
    image = images[idx].permute(1, 2, 0).numpy()  # Convert image to HWC format and numpy array
    boxes = targets[idx]['boxes'].numpy()  # Convert to numpy array
    labels = targets[idx]['labels']  # Tensor of labels
    fig, ax = plt.subplots(1, figsize=(12, 9))
    ax.imshow(image)
    for box, label in zip(boxes, labels):
        box = box.tolist()
        # Convert box to format (x0, y0, x1, y1)
        x0, y0, x1, y1 = box
        width = x1 - x0
        height = y1 - y0 

        rect = patches.Rectangle((x0, y0), width, height, linewidth=1, edgecolor='r', facecolor='none')
        ax.add_patch(rect)
        plt.text(x0, y0, label_dict[label.item()], color='red', fontsize=12, bbox=dict(facecolor='yellow', alpha=0.5))
    plt.show()
 
def train_model(model, dataloaders, criterion, optimizer, num_epochs=2):
    for epoch in range(num_epochs):
        print(f'Epoch {epoch}/{num_epochs - 1}')
        print('-' * 10)

        model.train()  # Set the model to training mode
        
        for images, targets in dataloaders:
            images = [image.to(device) for image in images]
            #targets = [{k: v.to(device) for k, v in t.items()} for t in targets]
            targets = [{key: value.to(device) for key, value in target.items()} for target in targets]


            optimizer.zero_grad()  # Zero the parameter gradients

            loss_dict = model(images, targets)  # Pass both images and targets during training
            losses = sum(loss for loss in loss_dict.values())  # Sum the losses from the different heads

            losses.backward()
            optimizer.step()

        print(f'Epoch {epoch} loss: {losses.item()}')

    torch.save(model, 'test_code_2/rcnn_training/custom_resnet_fasterrcnn_2.pt')
    return model


def set_parameter_requires_grad(model):
    # Freeze all the parameters in the model
    for param in model.parameters():
        param.requires_grad = False
    
    # Allow training only for the box_predictor (classification head)
    for param in model.roi_heads.box_predictor.parameters():
        param.requires_grad = True


params_to_update = [p for p in custom_model.parameters() if p.requires_grad]
criterion = nn.CrossEntropyLoss()

optimizer = optim.SGD(params_to_update, lr=0.001, momentum=0.9)

def main():
    # display_image_with_boxes(image, boxes, labels, mydata.labels_dict)
    print('bob le sponge ')
    # display_image_with_boxes(train_dataloader, 1, mydata.labels_dict) # only 0 through 2????f
    
    set_parameter_requires_grad(custom_model)

    train_model(custom_model, train_dataloader, criterion, optimizer, 30)

    # print(collate_fn(mydataset))  # if you want to view the labels of the training dataset

if __name__ == '__main__':
    main()